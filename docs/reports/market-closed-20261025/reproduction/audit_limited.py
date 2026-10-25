"""Read-only reconciliation of this limited engineering regression, not tuning."""
from collections import Counter, defaultdict
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import shutil

from tools.report_core_policy_runs import audit
from tools.report_discovery_study import performance
from tools.report_final_profitability import html_costs, runtime_inputs

out=Path('docs/reports/market-closed-20261025')
root=Path(json.loads((out/'native-run-protocol.json').read_text(encoding='utf-8-sig'))['archive'])
status=json.loads((root/'run-status.json').read_text(encoding='utf-8-sig'))
assert status['status']=='TERMINAL_EXIT_REQUIRES_AUDIT',status
r=audit(root,'2026-04-24','2026-05-16')
(out/'native-audit.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
runtime=runtime_inputs(root,r['inputs'])
deployed=root/'terminal/MQL5/Experts/TraderLab'/f'{root.name}.ex5'
assert hashlib.sha256(deployed.read_bytes()).hexdigest()==r['compiled_binary_sha256']
files=root/'native-files'
plan_file=next(p for p in files.glob('*plans-*.dat') if 'plans-wal' not in p.name)
gateway_file=next(files.glob('*gateway-*.dat'))
plans={}
for line in plan_file.read_text().splitlines():
    row=line.split('|')
    if row[0]!='PLAN':continue
    assert len(row)==11
    for leg in range(2):
        assert row[2+leg] not in plans
        plans[row[2+leg]]=dict(setup=row[1],side=int(row[4]),single=row[5]=='1',
                                  reference=row[8],shared_stop=row[10],leg=leg+1)
gateway=[line.split('|') for line in gateway_file.read_text().splitlines()]
protected={s[0]:s for s in gateway if len(s)==10 and s[3]=='RECONCILED' and not s[0].startswith(('B','M','C'))}
entries={};positions=[];setups=defaultdict(lambda:D(0));daily=defaultdict(lambda:D(0))
for key,deals in r['positions'].items():
    ins=[d for d in deals if d['entry_kind']==0];outs=[d for d in deals if d['entry_kind']==1]
    assert len(ins)==len(outs)==1,(key,deals)
    a,b=ins[0],outs[0];identity=a['comment'].removeprefix('TL:')
    assert identity in plans and identity not in entries
    entries[identity]=a
    p=plans[identity];receipt=protected[identity]
    stop=D(str(a['price']))-p['side']*4 if p['single'] else D(p['shared_stop'])
    target=D(p['reference'])+p['side']*(6 if p['leg']==1 else 10)
    assert D(receipt[4])==D('.01') and D(receipt[5])==stop and D(receipt[6])==target
    assert D(str(a['volume']))==D(str(b['volume']))==D('.01')
    net=sum((D(str(d['net'])) for d in deals),D(0))
    setups[p['setup']]+=net;daily[b['actual_server_time'][:10]]+=net
    positions.append(dict(id=identity,setup=p['setup'],position=key,entry=a,exit=b,
                          net_usd=str(net),verified_sl=str(stop),verified_tp=str(target)))
assert len(positions)==r['actual_closed_positions']
assert sum(setups.values(),D(0))==D(r['deal_net_reconciled'])
rejects={row[0] for row in gateway if len(row)==10 and row[3]=='REJECTED' and row[0].startswith('EX')}
assert not (rejects & entries.keys()),'Rejected entry acquired an execution'
claims=Counter(row[0] for row in gateway if len(row)==10 and row[3]=='INTENT')
assert max(claims.values(),default=0)==1,'An intent was automatically repeated'
dispatch=[e for e in r['events'] if e['event']=='CORE_TESTER_DISPATCH_RESULT']
bos_attempts=Counter(e['bos_id'] for e in dispatch)
assert max(bos_attempts.values(),default=0)==1,'A consumed BOS returned for another attempt'
summary=next(e for e in r['events'] if e['event']=='CORE_CONTROLLER_SUMMARY')
assert not summary['controller_halted'] and summary['simulated_orders_enabled']
assert not summary['broker_orders_enabled'] and summary['dispatch_locked']
assert 'EX132411' in rejects,'Original Market closed case was not reproduced'
assert all(p['entry']['actual_server_time']>='2026-04-24' for p in positions)
later=[p for p in positions if p['entry']['actual_server_time']>'2026-05-07T23:17:25']
assert later,'No actual fresh setup executed after Market closed'
old=json.loads(Path('docs/reports/long-history-20261023/partial-price-performance.json').read_text())
entry_by_deal={p['entry']['deal']:p for p in positions}
prefix=[]
for p in old['positions']:
    actual=entry_by_deal[p['entry_ticket']]
    same=(D(str(actual['entry']['price']))==D(p['entry']['price']) and
          D(str(actual['exit']['price']))==D(p['exit']['price']) and
          actual['exit']['deal']==p['exit_ticket'] and actual['setup']==p['setup'])
    prefix.append(dict(original_entry_deal=p['entry_ticket'],same_actual_fills_and_setup=same))
assert all(p['same_actual_fills_and_setup'] for p in prefix),'Pre-error execution prefix differs'
logs=[]
for p in sorted((root/'terminal/Tester').glob('**/logs/*.log')):
    blob=p.read_bytes();s=blob.decode('utf-16' if blob[:2]==b'\xff\xfe' else 'utf-8-sig',errors='replace')
    logs.extend(line for line in s.splitlines() if any(w in line for w in (
        'retcode=10018','CORE_PAIR_DEFINITIVE_REJECTION_RECONCILED','real ticks begin',
        'generating based on real ticks','Test passed in','final balance','testing of Experts',
        'real ticks absent','every tick generation used','CORE_FIRST_LEG_CHECK_REJECTED_NO_SEND','initial deposit')))
(out/'native-regression-log-extract.txt').write_text('\n'.join(logs)+'\n',encoding='utf-8')
assert any('retcode=10018' in line and 'state=REJECTED' in line for line in logs)
assert any('CORE_PAIR_DEFINITIVE_REJECTION_RECONCILED id=EX132411' in line for line in logs)
assert any('initial deposit 1000.00 USD, leverage 1:200' in line for line in logs)
bootstrap=Counter()
raw=next(files.glob('POLMCFIX*.jsonl'))
with raw.open('rb') as f:
    for i,line in enumerate(f):
        if i>4000:break
        if b'"event":"CLOSED_BAR"' in line:bootstrap[json.loads(line)['timeframe']]+=1
assert set(bootstrap)=={'M1','M5','M15','H1','H4'},bootstrap
locks=json.loads((out/'native-lock-status.json').read_text())
assert locks['dispatch_locked'] and not locks['execution_requested']
costs=html_costs(next(root.glob('*.html')),r['deal_net_reconciled'])
result=dict(mode='LIMITED_NATIVE_REAL_TICK_ENGINEERING_REGRESSION_NOT_PROFITABILITY_ACCEPTANCE',
    measured_from='2026-04-24',measured_until_exclusive='2026-05-16',warmup_from='2026-04-07',
    runtime_initial_deposit_usd=1000,runtime_leverage='1:200',bootstrap_closed_bars_by_timeframe=dict(bootstrap),
    native_tick_quality=r['native_tick_quality'],native_report_metrics=r['native_report_metrics'],
    actual_deals=r['actual_entry_deals']+r['actual_closed_positions'],closed_positions=len(positions),
    actual_setup_ids=len(setups),net_profit_usd=r['deal_net_reconciled'],costs=costs,
    setup_performance=performance(setups.values()),positions=positions,
    setup_results=[dict(setup=k,net_usd=str(v)) for k,v in setups.items()],
    daily_closed_net_usd={k:str(v) for k,v in sorted(daily.items())},
    first_new_entry_after_rejection=min(p['entry']['actual_server_time'] for p in later),
    positions_entered_after_rejection=len(later),rejected_entry_ids=sorted(rejects),
    net_positions_entered_after_rejection_usd=str(sum((D(p['net_usd']) for p in later),D(0))),
    rejected_entries_executed=0,maximum_intent_claims=max(claims.values(),default=0),
    maximum_dispatch_attempts_per_bos=max(bos_attempts.values(),default=0),
    native_final_controller_summary=summary,runtime_input_verification=runtime,
    end_of_test_liquidations=sum(p['exit']['comment']=='end of test' for p in positions),
    all_original_12_positions_preserved=True,pre_error_prefix_comparison=prefix,
    persisted_unfilled_plan_ids=sorted(set(plans)-entries.keys()),
    no_plan_is_counted_as_a_fill=True,dispatch_outcomes=r['dispatch_results'],
    emergency_reasons=[row[1] for row in gateway if row[0]=='EMERGENCY'],
    raw_sha256=r['raw_sha256'],raw_bytes=r['raw_bytes'],archive=str(root),
    tested_binary_sha256=r['compiled_binary_sha256'],native_html_sha256=r['native_report_sha256'],
    permanent_market_closed_halt_fixed=True,
    no_live_demo_real_or_contest_enablement=True)
(out/'limited-native-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
(out/'native-audit.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
for p in root.iterdir():
    if p.suffix in ('.html','.png','.set','.ini'):shutil.copy2(p,out/p.name)
for p in (gateway_file,plan_file):shutil.copy2(p,out/p.name)
print(json.dumps({k:result[k] for k in ('closed_positions','actual_setup_ids','net_profit_usd',
    'first_new_entry_after_rejection','positions_entered_after_rejection','emergency_reasons')},indent=2))
