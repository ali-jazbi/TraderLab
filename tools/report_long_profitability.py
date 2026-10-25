"""Reconcile the prespecified continuous six-month Native study, without tuning."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import shutil

from tools.report_core_policy_runs import audit
from tools.report_discovery_study import analyze, performance
from tools.report_final_profitability import html_costs, runtime_inputs, sample_units, execution_observations
from tools.report_body80_study import structural_proof


def monthly_results(r, p):
    months={f'2026-{m:02d}':dict(month=f'2026-{m:02d}',cash_net=D(0),deal_count=0,
            positions_entered=0,new_setup_ids=[],cohort_returns=[]) for m in range(4,11)}
    setups=defaultdict(list)
    for position in p['actual_positions']:
        setups[position['setup']].append(position)
        months[position['entry_time'][:7]]['positions_entered']+=1
    for deals in r['positions'].values():
        for deal in deals:
            month=deal['actual_server_time'][:7]
            months[month]['cash_net']+=D(str(deal['net']))
            months[month]['deal_count']+=1
    for setup, positions in setups.items():
        month=min(v['entry_time'] for v in positions)[:7]
        net=sum((D(v['net']) for v in positions),D(0))
        months[month]['new_setup_ids'].append(setup)
        months[month]['cohort_returns'].append(net)
    result=[]
    for month, row in months.items():
        stats=performance(row.pop('cohort_returns'))
        row['cash_net']=str(row['cash_net'])
        row['first_entry_setup_cohort']=stats
        row['new_setup_ids'].sort()
        row['period_start_server']='2026-04-24' if month=='2026-04' else month+'-01'
        row['period_until_exclusive_server']='2026-10-24' if month=='2026-10' else f"2026-{int(month[-2:])+1:02d}-01"
        result.append(row)
    actual=sum((D(v['cash_net']) for v in result),D(0))
    cohorts=sum((D(v['first_entry_setup_cohort']['net']) for v in result),D(0))
    if actual!=cohorts or actual!=D(p['position_performance']['net']):
        raise ValueError('Monthly deal cash and complete setup returns do not reconcile')
    if sum(v['first_entry_setup_cohort']['count'] for v in result)!=len(setups):
        raise ValueError('A setup was omitted or counted in multiple entry cohorts')
    return result


def calendar_execution_checks(p, manifest):
    utc=timezone.utc;offset=timedelta(hours=3)
    source=Path(manifest['calendar_file'])
    days=[];news=[]
    for line in source.read_text().splitlines():
        f=line.split('|')
        if f[0]=='DAY':days.append((f[1],datetime.fromtimestamp(int(f[2]),utc),datetime.fromtimestamp(int(f[3]),utc),datetime.fromtimestamp(int(f[4]),utc)))
        elif f[0]=='NEWS':news.append((f[1],datetime.fromtimestamp(int(f[2]),utc),datetime.fromtimestamp(int(f[4]),utc)))
    errors=[]
    for position in p['actual_positions']:
        entry=datetime.fromisoformat(position['entry_time']).replace(tzinfo=utc)-offset
        exit=datetime.fromisoformat(position['exit_time']).replace(tzinfo=utc)-offset
        active=[d for d in days if d[1]<=entry<d[2] and d[3]<=entry]
        if len(active)!=1:errors.append(dict(position=position['position'],reason='ENTRY_OUTSIDE_AVAILABLE_TRADING_DAY'))
        for name, at, known in news:
            if at-timedelta(minutes=15)<=entry<=at+timedelta(minutes=15):
                errors.append(dict(position=position['position'],event=name,at=at.isoformat(),reason='ENTRY_DURING_NEWS_RESTRICTION'))
            deadline=at-timedelta(seconds=180)
            if entry<=deadline<exit:
                errors.append(dict(position=position['position'],event=name,at=at.isoformat(),reason='POSITION_OPEN_AFTER_NEWS_DEADLINE'))
    return dict(checked_positions=len(p['actual_positions']),news_events=len(news),violations=errors,
                valid=not errors,scope='Actual fills against the unchanged session policy and canonical +/-15 minute entry/180 second closure limits; no simulated repair or trade removal.')


def bootstrap_evidence(raw):
    frames={tf:[] for tf in ('M1','M5','M15','H1','H4')}
    with raw.open('rb') as file:
        for index,line in enumerate(file):
            if index>=10000:break
            if b'"event":"BOS_TRACKER_CLOSED_BAR"' not in line:continue
            event=json.loads(line)
            if event['before_tick_index']==1:frames[event['timeframe']].append(event['opened_at'])
    result={tf:dict(closed_bars=len(values),first_opened_at=min(values) if values else None,last_opened_at=max(values) if values else None) for tf,values in frames.items()}
    if not all(r['closed_bars']==21 for r in result.values()):raise ValueError('Missing frozen21-bar bootstrap on an active timeframe')
    if min(r['first_opened_at'] for r in result.values())<'2026-03-29T00:00:00':raise ValueError('Bootstrap reaches outside the validated GMT+3 season')
    return result


def native_month_tick_crosscheck(raw, coverage):
    """Compare captured tick histograms with independent Native callbacks."""
    months=[f'2026-{m:02d}' for m in range(5,11)]
    expected={v['month'][:7].replace('.','-'):v['callbacks'] for v in coverage['months']}
    if not all(month in expected for month in months):
        raise ValueError('Independent Native coverage audit lacks a comparison month')
    observed=Counter();days=Counter()
    with raw.open('rb') as file:
        for line in file:
            if b'"event":"TICK"' in line:
                stamp=line.split(b'"server_time":"',1)[1]
                month=stamp[:7].decode('ascii');days[stamp[:10].decode('ascii')]+=1
                observed[month]+=1
    compared=[dict(month=month,independent_native_callbacks=expected[month],
                   captured_native_ticks=observed[month],matches=expected[month]==observed[month]) for month in months]
    if not all(row['matches'] for row in compared):
        raise ValueError('Native tick histogram differs from independent data audit; inspect feed revisions or capture gaps: '+str(compared))
    return dict(matches=True,months=compared,all_captured_ticks_by_server_month=dict(sorted(observed.items())),
        all_captured_ticks_by_server_day=dict(sorted(days.items())),
        scope='May through September complete months, October1–23 shared end. April is partial and excluded from equality, not deleted from the strategy result. Native HTML total ticks are not substituted for callback counts; no arbitrary count tolerance is applied.')


def report(archive, out, evidence):
    frozen=json.loads((evidence/'frozen-candidate.json').read_text())
    protocol=json.loads((evidence/'six-month-run-protocol.json').read_text(encoding='utf-8-sig'))
    calendar=json.loads((evidence/'six-month-calendar.manifest.json').read_text())
    storage=archive/'ntfs-storage-control.json'
    if storage.exists():
        control=json.loads(storage.read_text())
        if not control.get('stable_prefix_unchanged') or control.get('ea_or_strategy_inputs_changed'):
            raise ValueError('Unverified storage-control integrity; do not accept the Native result')
    for filename, expected in frozen['source_sha256'].items():
        if hashlib.sha256(Path(filename).read_bytes()).hexdigest()!=expected:raise ValueError('Frozen strategy source changed: '+filename)
    for filename, sha in protocol['hashes'].items():
        path=archive/filename
        if filename=='TraderLab-auto-tester-calendar.csv':path=archive/'native-files'/filename
        if hashlib.sha256(path.read_bytes()).hexdigest()!=sha:raise ValueError('Sealed run file changed: '+filename)
    r=audit(archive,'2026-04-24','2026-10-24')
    if r['compiled_binary_sha256']!=frozen['tested_binary_sha256']:raise ValueError('Frozen EA binary changed')
    expected={k:v for k,v in frozen['parameters'].items() if k not in ('InpLogFile','InpTesterCoreExecutionFromServer')}
    actual={k:v for k,v in r['inputs'].items() if k not in ('InpLogFile','InpTesterCoreExecutionFromServer')}
    if expected!=actual or r['inputs']['InpTesterCoreExecutionFromServer']!='2026.04.24 00:00:00':raise ValueError('Strategy parameters changed')
    runtime=runtime_inputs(archive,r['inputs'])
    logs=[]
    for path in (archive/'terminal/Tester').glob('Agent-*/logs/*.log'):
        blob=path.read_bytes();logs.append(blob.decode('utf-16' if blob[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig',errors='replace'))
    if not any('initial deposit 1000.00 USD, leverage 1:200' in text for text in logs):raise ValueError('Native capital/leverage mismatch')
    ini=next(archive.glob('POLLONG*.ini')).read_text(encoding='utf-16')
    for line in ('Model=4','ExecutionMode=0','Optimization=0','FromDate=2026.04.07','ToDate=2026.10.24','AllowLiveTrading=0'):
        if line not in ini.splitlines():raise ValueError('Changed test setting: '+line)
    p=analyze(r);raw=next((archive/'native-files').glob('POLLONG*.jsonl'))
    tick_months=native_month_tick_crosscheck(raw,json.loads((evidence/'broker-tick-coverage.json').read_text()))
    seed=bootstrap_evidence(raw)
    costs=html_costs(next(archive.glob('POLLONG*.html')),p['position_performance']['net'])
    if costs['deal_rows']!=sum(len(v) for v in r['positions'].values()):raise ValueError('Deal multiplicity mismatch')
    calendar_check=calendar_execution_checks(p,dict(calendar_file=str(archive/'native-files/TraderLab-auto-tester-calendar.csv')))
    monthly=monthly_results(r,p)
    units=sample_units(p['actual_positions']);execution=execution_observations(p['actual_positions'])
    structure=structural_proof(raw)
    per_tf={tf:performance(D(v['net']) for v in p['setup_results'] if v['setup'].split(':',2)[1]==tf) for tf in ('M1','M5','M15','H1','H4')}
    metric=next(v for v in r['events'] if v['event']=='TESTER_CORE_METRICS')
    criteria=frozen['acceptance'];missing=['HISTORICAL_ALL_IN_BROKER_COSTS_NOT_CERTIFIED','ZERO_LATENCY_SLIPPAGE_TAIL_NOT_CERTIFIED','STATISTICAL_SETUP_INDEPENDENCE_NOT_CERTIFIED','PART_OF_OCTOBER_WAS_PREVIOUSLY_INSPECTED']
    missing += ['UNSET_'+key.upper() for key in ('maximum_drawdown','minimum_independent_setups','minimum_separate_windows') if criteria.get(key) is None]
    if not calendar_check['valid']:missing.append('CALENDAR_EXECUTION_VIOLATION')
    # An honest completed historical estimate is distinct from a final PASS.
    result=dict(status='INSUFFICIENT_EVIDENCE',reasons=missing,
        native_strategy_test_complete=True,real_tick_feed_verified=r['native_tick_quality']['real_ticks_only_verified'],
        independent_native_month_counts_match=tick_months['matches'],
        calendar_dates_and_pre_event_sources_validated=True,calendar_execution_valid=calendar_check['valid'],
        source_asof_limit='Dated public announcements and documented schedule derivation; no cryptographic historical snapshot feed.',
        candidate=frozen['candidate'],binary_sha256=frozen['tested_binary_sha256'],
        archive=str(archive),raw_sha256=r['raw_sha256'],measured_server_window=r['measured_server_window'],
        warmup_from_server='2026-04-07',measurement_calendar_days=183,continuous_account_no_monthly_resets=True,
        initial_capital_usd='1000.00',net_after_tester_costs=p['position_performance']['net'],
        setup_statistics=p['setup_performance'],native_report_statistics=p['native_report_metrics'],
        unique_setups=units['unique_setups'],overlap_or_shared_impulse_clusters=len(units['overlap_or_shared_impulse_clusters']),
        position_legs=p['position_performance']['count'],actual_deals=costs['deal_rows'],
        maximum_native_equity_drawdown_usd=metric['max_equity_drawdown'],
        measured_real_ticks=r['measured_ticks'],warmup_real_ticks=r['warmup_ticks'],
        end_of_test_liquidations=p['end_of_test_liquidations'],
        end_of_test_liquidation_position_net=str(sum((D(v['net']) for v in p['actual_positions'] if v['exit_comment']=='end of test'),D(0))),
        all_trades_and_losses_retained=True,no_outcome_based_parameters_or_filters=True,
        monthly=monthly,timeframes=per_tf,
        monthly_basis='Cash net uses each real deal timestamp, including entry costs. Setup Win Rate/PF use complete net of all legs/repeated entries grouped by frozen setup ID and assigned once to its first-entry month. Cohorts can differ from cash when positions cross month end.',
        demo_dispatch_locked=True,real_enabled=False,contest_enabled=False,reverse_enabled=False)
    out.mkdir(parents=True,exist_ok=False)
    for name,value in [('results',r),('performance',p),('assessment',result),('monthly',monthly),('costs',costs),('runtime-inputs',runtime),('sample',units),('execution',execution),('calendar-execution',calendar_check),('bootstrap-timeframes',seed),('detection',structure),('tick-month-crosscheck',tick_months)]:
        (out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
    for path in archive.iterdir():
        if path.is_file() and path.suffix.lower() in ('.html','.png','.ini','.set','.json'):shutil.copy2(path,out/path.name)
    for path in (archive/'terminal').glob('**/logs/*.log'):
        dest=(out/path.relative_to(archive/'terminal')).with_suffix('.log.txt');dest.parent.mkdir(parents=True,exist_ok=True)
        b=path.read_bytes();text=b.decode('utf-16' if b[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig',errors='replace')
        if path.parent.parent==archive/'terminal':text='\n'.join(v for v in text.splitlines() if '\tNetwork\t' not in v)+'\n'
        dest.write_text(text,encoding='utf-8')
    journals=out/'reconciliation-journals';journals.mkdir()
    for glob in ('*plans-*.dat','*gateway-*.dat'):
        for path in (archive/'native-files').glob(glob):
            if path.stat().st_size>10_000_000:raise ValueError('Unexpectedly large reconciliation journal; preserve locally and inspect before publishing')
            shutil.copy2(path,journals/path.name)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,default=Path('docs/reports/long-history-20261023'))
    a=parser.parse_args();r=report(a.archive,a.out,a.evidence)
    print(json.dumps({k:r[k] for k in ('status','net_after_tester_costs','setup_statistics','position_legs','maximum_native_equity_drawdown_usd','monthly')},indent=2))
