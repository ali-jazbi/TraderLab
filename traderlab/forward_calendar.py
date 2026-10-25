"""Forward SDK calendar -> atomic live packet, with IANA session clocks.

Only genuinely observed US/USD native values are accepted. A failed/old snapshot
invalidates entries; it never gets a new observation time from this publisher.
"""
import argparse
from datetime import datetime, timedelta, time, timezone
import json
import os
from pathlib import Path
import time as clock
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

UTC = timezone.utc
PROVIDER = 'MT5_USD_PRIMARY_FORWARD_V1'
MAX_AGE = 180


def sessions(now):
    """Frozen Sydney 07 -> NY 17, next Sydney owns the overlap (as Tester)."""
    syd, ny = ZoneInfo('Australia/Sydney'), ZoneInfo('America/New_York')
    first = now.astimezone(syd).date() - timedelta(days=4)
    rows = []
    for i in range(10):
        day = first + timedelta(days=i)
        if day.weekday() >= 5:
            continue
        start = datetime.combine(day, time(7), syd).astimezone(UTC)
        ny_day = start.astimezone(ny).date() + timedelta(days=1)
        end = datetime.combine(ny_day, time(17), ny).astimezone(UTC)
        following = day + timedelta(days=1)
        while following.weekday() >= 5:
            following += timedelta(days=1)
        next_start = datetime.combine(following, time(7), syd).astimezone(UTC)
        rows.append((str(day), int(start.timestamp()), int(min(end, next_start).timestamp())))
    return rows


def packet(snapshot, now):
    observed = snapshot['observed_utc']
    epoch = int(now.timestamp())
    offset = snapshot['server_offset']
    if (snapshot.get('valid') is not True or snapshot.get('error') != 0 or
            not isinstance(observed, int) or not 0 <= epoch-observed < MAX_AGE or
            not isinstance(offset, int) or abs(offset) > 14*3600 or offset % 900):
        raise ValueError('NATIVE_SNAPSHOT_INVALID_OR_STALE')
    events, families = set(), set()
    ny = ZoneInfo('America/New_York')
    for value in snapshot['events']:
        code = value['code']
        name = ('CPI' if code.startswith('consumer-price-index') else
                'NFP' if code == 'nonfarm-payrolls' else
                'FOMC' if code in ('fed-interest-rate-decision', 'fomc-minutes', 'fomc-press-conference') else None)
        if name is None:
            raise ValueError('UNSUPPORTED_NEWS_CODE')
        host = urlparse(value['source']).hostname
        if (host not in (('bls.gov', 'www.bls.gov') if name != 'FOMC' else
                        ('federalreserve.gov', 'www.federalreserve.gov')) or value['time_mode'] != 0):
            raise ValueError('PRIMARY_SOURCE_OR_EXACT_NEWS_TIME_REQUIRED')
        at = value['server_time'] - offset
        local = datetime.fromtimestamp(at, UTC).astimezone(ny)
        expected = (8, 30) if name in ('CPI', 'NFP') else (14, 30) if code == 'fomc-press-conference' else (14, 0)
        if (local.hour, local.minute) != expected or local.second:
            # Includes ambiguous server clock/DST conversion. Never shift to fit.
            raise ValueError('PRIMARY_EVENT_CLOCK_MISMATCH')
        if at > observed:
            families.add(name)
        events.add((name, at))
    if families != {'CPI', 'NFP', 'FOMC'}:
        raise ValueError('INCOMPLETE_FORWARD_NEWS_FAMILIES')
    days = sessions(now)
    start, end = days[0][1], days[-1][2]
    rows = [f'SYDNEY_NY_NEWS_V2|{PROVIDER}|{start}|{end}|{observed}|{observed+MAX_AGE}']
    rows += [f'DAY|{day}|{a}|{b}|{observed}' for day, a, b in days]
    rows += [f'NEWS|{name}|{at}|0|{observed}' for name, at in sorted(events, key=lambda v: (v[1], v[0])) if start <= at <= end]
    return '\n'.join(rows)+'\n'


def publish(root, now=None):
    now = now or datetime.now(UTC)
    try:
        data = packet(json.loads((root/'TraderLab-forward-native.json').read_text(encoding='utf-8-sig')), now)
        status = 'VERIFIED'
    except (ValueError, KeyError, TypeError, OSError) as error:
        data, status = 'INVALID\n', str(error)
    target = root/'TraderLab-forward-calendar.csv'
    if not target.exists() or target.read_text(encoding='utf-8-sig') != data:
        temporary = target.with_suffix('.tmp')
        temporary.write_text(data, encoding='utf-8')
        os.replace(temporary, target)
    return status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--files', required=True, type=Path)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    last = None
    while True:
        try:
            status = publish(args.files)
        except OSError as error:
            status = f'PUBLISH_IO_BLOCKED:{error}'
        if status != last:
            print(datetime.now(UTC).isoformat(), status, flush=True)
            last = status
        if args.once:
            return
        clock.sleep(2)


if __name__ == '__main__':
    main()
