import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0,str(Path.cwd()))
from tools.report_core_policy_runs import native_tick_quality, Cells

base=Path('docs/reports/long-history-20261023')
work=Path('work/long-history-20261023')
utc=timezone.utc;ny=ZoneInfo('America/New_York');sydney=ZoneInfo('Australia/Sydney')
bls=json.loads((base/'bls-asof-proof.json').read_text())['events']
fed=json.loads((base/'fed-asof-proof.json').read_text())['events']
causal=json.loads((base/'fed-causal-asof-proof.json').read_text())
confirm={r['meeting_date']:r for r in causal['preceding_confirmations']}
clocks={r['date']:r for r in causal['publication_headers']}
historical=[json.loads(s) for s in (base/'historical-calendar-all-usd.jsonl').read_text().splitlines()]
historical=[r for r in historical if r['event']=='CALENDAR_VALUE']
first=date(2026,4,7);end=date(2026,10,24)
def local(d,t):return datetime.fromisoformat(d+'T'+t).replace(tzinfo=ny)
events=[]
for row in bls:
    at=local(row['scheduled_date_ny'],row['scheduled_time_ny']).astimezone(utc)
    known=local(row['source_publication_date_ny'],row['source_publication_time_ny']).astimezone(utc)
    code='nonfarm-payrolls' if row['family']=='NFP' else 'consumer-price-index-mm'
    events.append(dict(name=row['family'],at=at,available=known,code=code,sources=[row['source']],asof_method=row['evidence_method']))
for row in fed:
    d=date.fromisoformat(row['scheduled_date_ny'])
    if not first<=d<end:continue
    at=local(row['scheduled_date_ny'],row['scheduled_time_ny']).astimezone(utc)
    if row['subtype']=='FOMC Minutes':
        parent=(d-timedelta(days=21)).isoformat();publication=clocks[parent]
        known=local(parent,publication['published_ny_time']).astimezone(utc)
        code='fomc-minutes';sources=[publication['url'],causal['minutes_publication_policy_source'],row['source']]
        method='Public decision date plus the preexisting21-day14:00 ET publication policy; actual official calendar and native metadata agree. Derived schedule, not a claimed direct next-release quote.'
    else:
        previous=confirm[d.isoformat()]
        known=datetime.fromisoformat(previous['confirmation_publication_ny']).replace(tzinfo=ny).astimezone(utc)
        code='fomc-press-conference' if row['subtype']=='FOMC Press Conference' else 'fed-interest-rate-decision'
        sources=[previous['confirmation_source'],previous['publication_clock_source'],causal['annual_clock_source'],row['source']]
        method='Preceding published minutes explicitly confirm the next meeting; dated2024 announcement specifies statement14:00 and conference14:30 ET.'
    events.append(dict(name='FOMC',subtype=row['subtype'],at=at,available=known,code=code,sources=sources,asof_method=method))
events.sort(key=lambda v:v['at'])
assert len(events)==26
assert len({(e['name'],e['at']) for e in events})==26
for e in events:
    assert e['available']<=e['at']-timedelta(minutes=15)
    found=[r for r in historical if r['event_code']==e['code'] and datetime.strptime(r['server_time'],'%Y.%m.%d %H:%M').replace(tzinfo=timezone(timedelta(hours=3))).astimezone(utc)==e['at']]
    assert len(found)==1,(e,found)
    e['native_historical_metadata_match']=True

days=[];d=first
while d<end:
    if d.weekday()<5:
        opening=datetime.combine(d,datetime.min.time()).replace(hour=7,tzinfo=sydney).astimezone(utc)
        closing=datetime.combine(d,datetime.min.time()).replace(hour=17,tzinfo=ny).astimezone(utc)
        days.append(dict(id=d.isoformat(),opening=opening,closing=closing,available=opening))
    d+=timedelta(days=1)
for i,row in enumerate(days[:-1]):
    # Preserve the existing explicitly experimental overlap policy, without a
    # new session filter, holiday blacklist, or owner-amendment claim.
    row['closing']=min(row['closing'],days[i+1]['opening'])
epoch=lambda v:int(v.timestamp())
lines=[f"SYDNEY_NY_NEWS|EXPERIMENTAL_TESTER_ONLY:overlap_clipped_at_next_sydney_open:PRIMARY_PREANNOUNCED_NEWS|{epoch(days[0]['opening'])}|{epoch(days[-1]['closing'])}"]
lines += [f"DAY|{r['id']}|{epoch(r['opening'])}|{epoch(r['closing'])}|{epoch(r['available'])}" for r in days]
lines += [f"NEWS|{e['name']}|{epoch(e['at'])}|0|{epoch(e['available'])}" for e in events]
path=base/'six-month-calendar.csv';path.write_text('\n'.join(lines)+'\n',encoding='utf-8')

# Existing October decisions must be identical despite stronger source/as-of
# metadata. No historical outcome is used to change an entry or rejection.
old=(Path('docs/reports/final-profitability-20261023/candidate-calendar.csv').read_text().splitlines())
new_days={s.split('|')[1]:s.split('|')[2:4] for s in lines if s.startswith('DAY|')}
for line in old:
    p=line.split('|')
    if p[0]=='DAY' and p[1] in new_days:assert new_days[p[1]]==p[2:4]
    if p[0]=='NEWS':assert any(n.split('|')[0:4]==p[0:4] for n in lines if n.startswith('NEWS|'))
manifest=dict(status='PRIMARY_SCHEDULES_VALIDATED_BEFORE_STRATEGY_OUTCOMES',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
              historical_asof_availability_proved=True,asof_evidence_level='Dated primary preannouncements and explicitly documented institutional publication schedule; not cryptographically timestamped snapshots',
              immutable_historical_snapshot_feed=False,publisher_template_last_update_used_as_asof_witness=False,
              calendar_scope='TESTER_ONLY; unchanged experimental day-overlap policy; no live/Demo approval',
              utc_mapping='America/New_York publication clocks; fixed broker10800 seconds is valid for this entire chosen summer window',
              sessions=dict(sydney_local='07:00',new_york_local='17:00',availability='Conservative day-opening clock instant under the frozen profile, not invented publication timestamps',october_previous_study_start_end_match=True),
              day_count=len(days),news_count=len(events),events=[{k:v.isoformat() if isinstance(v,datetime) else v for k,v in e.items()} for e in events])
(base/'six-month-calendar.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

native_root=Path((work/'native-root.txt').read_text())
log=next((native_root/'terminal/Tester').glob('Agent-*/logs/*.log'))
text=log.read_text(encoding='utf-16')
import re,shutil
months=[json.loads(m) for m in re.findall(r'DATA_AUDIT_MONTH (\{[^\r\n]+\})',text)]
assert len(months)==13 and 'DATA_AUDIT_COMPLETE' in text
quality=native_tick_quality(native_root)
assert quality['unverified_interval_before_real_tick_start'] and not quality['real_ticks_only_verified']
boundary='2026.01.02 00:00:00'
generated=sum(r['callbacks'] for r in months if r['last_server']<boundary)
real=sum(r['callbacks'] for r in months if r['first_server']>=boundary)
assert generated+real==sum(r['callbacks'] for r in months),'A month straddles the real-tick boundary; do not invent its split'
scope=base/'native-year-data-audit';scope.mkdir(exist_ok=True)
shutil.copy2(log,scope/'completed-agent.log.txt')
for p in (native_root/'terminal').glob('NativeCoverageAudit.*'):shutil.copy2(p,scope/p.name)
for p in native_root.glob('*.ini'):shutil.copy2(p,scope/p.name)
summary=dict(scope='DATA_AUDIT_ONLY; no strategy orders or profitability assessment',requested=['2025-10-01','2026-10-24 exclusive'],
             native_completed=True,first_reported_real_tick_day='2026-01-02',last_real_tick_day='2026-10-23',
             qualified_scope='Observed LiteFinance-MT5-Demo / XAUUSD_o response for this requested year; not a global retention guarantee for every account',
             generated_2025_callbacks=generated,real_2026_callbacks=real,months=months,quality=quality,
             all_five_timeframes_seeded=all(f'DATA_AUDIT_TIMEFRAME PERIOD_{tf} bars=25 error=0' in text for tf in ['M1','M5','M15','H1','H4']),
             no_real_tick_absent_or_generation_warning='real ticks absent' not in text and 'every tick generation used' not in text,
             generated_prefix_rejected=True)
(base/'broker-tick-coverage.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(dict(days=len(days),news=len(events),calendar_sha256=manifest['sha256'],generated_prefix_callbacks=generated,real_2026_callbacks=real,all_timeframes=summary['all_five_timeframes_seeded'])))
