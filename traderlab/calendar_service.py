"""Forward-only primary calendar refresh. No historical availability is invented.

Unknown schemas, failed fetches and overlapping trading days invalidate entries.
Session clocks are the existing sourced broker profile, not new strategy rules.
"""
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo
import calendar
import hashlib
import json
import os
import re
import urllib.request
import uuid

UTC = timezone.utc


class CalendarUnavailable(ValueError):
    pass


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.lines, self.rows, self.row, self.cell = [], [], None, None
        self.hidden = 0
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1
        if tag == 'tr':
            self.row = []
        if tag in ('td', 'th'):
            self.cell = []

    def handle_data(self, value):
        value = ' '.join(value.split())
        if value and not self.hidden:
            self.lines.append(value)
            if self.cell is not None:
                self.cell.append(value)

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden = max(0, self.hidden - 1)
        if tag in ('td', 'th') and self.cell is not None:
            if self.row is not None:
                self.row.append(' '.join(self.cell))
            self.cell = None
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def event(name, local, source, known):
    aware = local.replace(tzinfo=ZoneInfo('America/New_York'))
    return {'name': name, 'scheduled_at': aware.astimezone(UTC).isoformat(),
            'available_at': known.isoformat(), 'source': source}


def parse_bls(text, year, month, source, known):
    page = Page(text)
    if f'{calendar.month_name[month]} {year}' not in page.lines:
        raise CalendarUnavailable('BLS_MONTH_SCHEMA_OR_COVERAGE')
    found = []
    for row in page.rows:
        if len(row) != 3:
            continue
        day, clock, title = row
        name = 'NFP' if title.startswith('Employment Situation') else 'CPI' if title.startswith('Consumer Price Index') else None
        if name:
            try:
                local = datetime.strptime(day + ' ' + clock, '%A, %B %d, %Y %I:%M %p')
            except ValueError as error:
                raise CalendarUnavailable('BLS_UNSCHEDULED_OR_CHANGED_SCHEMA') from error
            if (local.year, local.month) != (year, month):
                raise CalendarUnavailable('BLS_WRONG_MONTH')
            found.append(event(name, local, source, known))
    if {v['name'] for v in found} != {'CPI', 'NFP'}:
        raise CalendarUnavailable('BLS_INCOMPLETE_MONTH_NOT_AN_EMPTY_NEWS_WINDOW')
    return found


def parse_fed(text, year, month, source, known):
    lines = Page(text).lines
    if f'{calendar.month_name[month]} {year}' not in lines or 'FOMC Meetings' not in lines:
        raise CalendarUnavailable('FED_MONTH_SCHEMA_OR_COVERAGE')
    start = lines.index('FOMC Meetings') + 1
    end = next((i for i in range(start, len(lines)) if lines[i] in ('Beige Book', 'Statistical Releases', 'Other')), len(lines))
    section = lines[start:end]
    clocks = [(i, re.fullmatch(r'(\d{1,2}):(\d{2})\s*([ap])\.?m\.?', v, re.I)) for i, v in enumerate(section)]
    clocks = [(i, m) for i, m in clocks if m]
    found = []
    for n, (i, match) in enumerate(clocks):
        block = section[i+1:clocks[n+1][0] if n+1 < len(clocks) else len(section)]
        days = [int(v) for v in block if re.fullmatch(r'[1-9]|[12]\d|3[01]', v)]
        if len(days) != 1 or not any('FOMC' in v for v in block):
            raise CalendarUnavailable('FED_UNSCHEDULED_OR_CHANGED_SCHEMA')
        hour = int(match[1]) % 12 + (12 if match[3].lower() == 'p' else 0)
        found.append(event('FOMC', datetime(year, month, days[0], hour, int(match[2])), source, known))
    # No parsed meeting is only allowed with an explicit upstream "None" section.
    if not found and not any(v.lower() in ('none', 'no meetings scheduled') for v in section):
        raise CalendarUnavailable('FED_EMPTY_SECTION_NOT_COVERAGE_PROOF')
    return found


def fetch_primary(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'TraderLab-Calendar/1.0 (primary schedule validation)'})
    with urllib.request.urlopen(request, timeout=15) as response:
        if response.status != 200 or response.geturl() != url:
            raise CalendarUnavailable('PRIMARY_SOURCE_REDIRECT_OR_STATUS')
        raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise CalendarUnavailable('PRIMARY_SOURCE_TOO_LARGE')
        return raw.decode('utf-8-sig'), datetime.now(UTC)


def session(day, profile):
    clocks = (('sydney_open', 'Australia/Sydney'), ('new_york_close', 'America/New_York'))
    result = []
    for key, zone in clocks:
        hour, minute = map(int, profile[key].split(':'))
        result.append(datetime.combine(day, datetime.min.time()).replace(hour=hour, minute=minute, tzinfo=ZoneInfo(zone)).astimezone(UTC))
    if result[1] <= result[0]:
        raise CalendarUnavailable('INVALID_SESSION_WINDOW')
    return tuple(result)


def prepare(now, day, profile, max_age_seconds, fetch=fetch_primary, previous=None):
    if now.tzinfo is None or now.utcoffset() != timedelta(0) or max_age_seconds <= 0 or max_age_seconds > 3600:
        raise CalendarUnavailable('EXPLICIT_UTC_AND_MAXIMUM_ONE_HOUR_FRESHNESS_REQUIRED')
    if day.weekday() >= 5 or not profile.get('source', '').startswith('https://www.litefinance.org/'):
        raise CalendarUnavailable('WEEKEND_OR_UNSOURCED_SESSION_PROFILE')
    opening, closing = session(day, profile)
    if closing <= now or opening > now + timedelta(days=4):
        raise CalendarUnavailable('EXPIRED_OR_UNREVIEWABLE_FORWARD_WINDOW')
    if previous and previous['day'] != day.isoformat() and opening < datetime.fromisoformat(previous['session_end_utc']):
        raise CalendarUnavailable('TODO_STRATEGY_UNRESOLVED:DAY_OVERLAP')
    if previous and previous['day'] == day.isoformat() and (previous['session_start_utc'], previous['session_end_utc']) != (opening.isoformat(), closing.isoformat()):
        raise CalendarUnavailable('SESSION_DEFINITION_MUTATED')
    months = {(opening.year, opening.month), (closing.year, closing.month)}
    events, evidence = [], []
    observed = now
    for year, month in sorted(months):
        sources = [(f'https://www.bls.gov/schedule/{year}/{month:02d}_sched_list.htm', parse_bls),
                   (f'https://www.federalreserve.gov/newsevents/{year}-{calendar.month_name[month].lower()}.htm', parse_fed)]
        for url, parse in sources:
            response = fetch(url)  # No fallback to expired cache or guessed empty events.
            # The live provider timestamps AFTER response completion. String-only
            # injected fixtures deliberately use the supplied synthetic clock.
            text, fetched = response if isinstance(response, tuple) else (response, now)
            if fetched.tzinfo is None or fetched.utcoffset() != timedelta(0) or fetched < now:
                raise CalendarUnavailable('PROVIDER_OBSERVATION_CLOCK_INVALID')
            observed = max(observed, fetched)
            events.extend(parse(text, year, month, url, fetched))
            evidence.append({'url': url, 'fetched_at': fetched.isoformat(), 'sha256': hashlib.sha256(text.encode()).hexdigest()})
    if observed >= closing:
        raise CalendarUnavailable('SOURCE_FINISHED_AFTER_SESSION_EXPIRY')
    expires = min(closing, observed + timedelta(seconds=max_age_seconds))
    epoch = lambda t: int(t.timestamp())
    header = f'SYDNEY_NY_NEWS_V2|PRIMARY_BLS_FED_FORWARD_V1|{epoch(opening)}|{epoch(closing)}|{epoch(observed)}|{epoch(expires)}'
    rows = [header, f'DAY|{day.isoformat()}|{epoch(opening)}|{epoch(closing)}|{epoch(observed)}']
    seen = set()
    for value in events:
        at = datetime.fromisoformat(value['scheduled_at'])
        key = value['name'], at
        if opening <= at <= closing and key not in seen:
            rows.append(f"NEWS|{value['name']}|{epoch(at)}|0|{epoch(observed)}")
            seen.add(key)
    manifest = {'day': day.isoformat(), 'session_start_utc': opening.isoformat(), 'session_end_utc': closing.isoformat(),
                'observed_at': observed.isoformat(), 'fresh_until': expires.isoformat(), 'sources': evidence,
                'automatic_demo_ready': False, 'scope': 'FORWARD_PRIMARY_SNAPSHOT_NO_INFERRED_DAY_OVERLAP'}
    return '\n'.join(rows)+'\n', manifest


def atomic_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.'+uuid.uuid4().hex+'.pending')
    with temporary.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


@contextmanager
def publisher_lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        if stream.tell() == 0:
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            if os.name == 'nt':
                stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def refresh(output, now, day, profile, max_age_seconds, fetch=fetch_primary):
    output = Path(output)
    metadata = output.with_suffix('.service.json')
    with publisher_lock(output.with_suffix('.publisher.lock')):
        try:
            previous = json.loads(metadata.read_text()) if metadata.exists() else None
            packet, manifest = prepare(now, day, profile, max_age_seconds, fetch, previous)
            # Preserve an immutable dated generation before replacing the active file.
            generation = output.parent/'calendar-evidence'/(now.strftime('%Y%m%dT%H%M%S%f')+'-'+uuid.uuid4().hex)
            generation.mkdir(parents=True)
            (generation/'packet.csv').write_text(packet, encoding='utf-8')
            (generation/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
            atomic_write(output, packet)
            atomic_write(metadata, json.dumps(manifest, indent=2)+'\n')
            return manifest
        except Exception as error:
            # An outage must invalidate entries immediately, even if old TTL remains.
            atomic_write(output, 'INVALID|CALENDAR_SOURCE_UNAVAILABLE\n')
            atomic_write(output.with_suffix('.failure.json'), json.dumps({'at': now.isoformat(), 'reason': str(error)})+'\n')
            raise
