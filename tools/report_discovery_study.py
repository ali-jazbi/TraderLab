"""Reconcile actual Tester deals with persisted Core plans and gateway protections.

Consumes report_core_policy_runs' strict, reconciled results. Never makes fills.
"""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal as D
import json
from pathlib import Path


def performance(values):
    values=list(values)
    profit=sum((v for v in values if v>0),D(0))
    loss=-sum((v for v in values if v<0),D(0))
    wins=sum(v>0 for v in values);losses=sum(v<0 for v in values)
    return dict(count=len(values),wins=wins,losses=losses,flat=len(values)-wins-losses,
                win_rate=str(D(wins)/len(values)) if values else None,
                net=str(sum(values,D(0))),net_unit_profit_factor=str(profit/loss) if loss else None)


def analyze(r):
    files=Path(r['archive'])/'native-files'
    plans={}
    for line in next(files.glob('*plans-*.dat')).read_text().splitlines():
        row=line.split('|')
        if row[0]!='PLAN':continue
        if len(row)!=11:raise ValueError('Malformed persisted Core plan')
        for leg in range(2):
            if row[2+leg] in plans:raise ValueError('Duplicate planned leg')
            plans[row[2+leg]]=dict(setup=row[1],side=int(row[4]),single=row[5]=='1',
                actual_be=row[7]=='1',reference=D(row[8]),planned=D(row[9]),shared_stop=D(row[10]),leg=leg+1)
    journal=[s.split('|') for s in next(files.glob('*gateway-*.dat')).read_text().splitlines()]
    protected={s[0]:s for s in journal if len(s)==10 and s[3]=='RECONCILED' and not s[0].startswith(('B','M','C'))}
    dispatch=[e for e in r['events'] if e['event']=='CORE_TESTER_DISPATCH_RESULT' and e['submitted']]
    positions=[];setups=defaultdict(list);daily=defaultdict(list);entries={};exits={}
    for key,deals in r['positions'].items():
        ins=[d for d in deals if d['entry_kind']==0];outs=[d for d in deals if d['entry_kind']==1]
        if len(ins)!=1 or len(outs)!=1:raise ValueError('Incomplete or partial position: '+key)
        entry,exit=ins[0],outs[0];identity=entry['comment'].removeprefix('TL:')
        p=plans[identity];entries[identity]=entry;exits[identity]=exit
        receipts=protected[identity]
        target=p['reference']+p['side']*(6 if p['leg']==1 else 10)
        stop=D(str(entry['price']))-p['side']*4 if p['single'] else p['shared_stop']
        if D(receipts[4])!=D('.01') or D(receipts[5])!=stop or D(receipts[6])!=target:
            raise ValueError('Actual-fill SL / shared TP / canonical volume mismatch: '+identity)
        if D(str(entry['volume']))!=D('.01') or D(str(exit['volume']))!=D('.01'):
            raise ValueError('Noncanonical deal volume')
        evidence=[e for e in dispatch if e['setup_id']==p['setup'] and
                  e['actual_signal_quote']['time_msc']==entry['deal_time_msc']]
        if len(evidence)!=1:raise ValueError('Entry lacks unique actual signal tick')
        if evidence[0]['server_time']<evidence[0]['frozen_group']['server_time']:
            raise ValueError('Entry precedes confirmed group availability')
        net=sum((D(str(d['net'])) for d in deals),D(0));setups[p['setup']].append(net)
        daily[entry['actual_server_time'][:10]].append(net)
        positions.append(dict(position=key,id=identity,setup=p['setup'],leg=p['leg'],
            single=p['single'],side=p['side'],planned=str(p['planned']),
            entry_time=entry['actual_server_time'],entry=str(entry['price']),
            exit_time=exit['actual_server_time'],exit=str(exit['price']),exit_comment=exit['comment'],
            net=str(net),stop=str(stop),target=str(target),
            actual_signal_quote=evidence[0]['actual_signal_quote']))
    if set(plans)!=set(entries):raise ValueError('Persisted plans and filled legs differ')
    be=[]
    for s in journal:
        if len(s)!=10 or not s[0].startswith('B') or s[3]!='RECONCILED':continue
        identity=s[0][1:];p=plans[identity];entry=entries[identity]
        anchor=D(str(entry['price'])) if p['single'] and p['actual_be'] else p['reference']
        expected=anchor+p['side']*D('.5')
        if p['leg']!=2 or D(s[5])!=expected:raise ValueError('BE anchor mismatch')
        peer=identity[:-1]+'1';tp=exits[peer]
        offset=int(r['inputs']['InpServerUtcOffsetSeconds'])
        if tp['reason']!=5 or tp['deal_time_msc']//1000-offset>int(s[9]):raise ValueError('BE without earlier actual TP1')
        be.append(dict(id=identity,stop=s[5],journal_utc_epoch_seconds=s[9]))
    pair_count=len(positions)//2
    if len(positions)%2 or pair_count!=len(dispatch):raise ValueError('Two-leg execution does not reconcile')
    exposure=maximum=D(0)
    for d in sorted((d for rows in r['positions'].values() for d in rows),
                    key=lambda d:(d['deal_time_msc'],d.get('deal',0))):
        exposure+=D(str(d['volume']))*(1 if d['entry_kind']==0 else -1)
        maximum=max(maximum,exposure)
        if exposure<0 or maximum>D('.04'):raise ValueError('Actual deal exposure violates study cap')
    if exposure:raise ValueError('Unclosed actual exposure')
    return dict(run=r['run'],policy=r['inputs'].get('InpExperimentalDiscoveryPolicy','0'),
        measured_server_window=r['measured_server_window'],
        structural_valid_new_groups=r['group_reasons'].get('ACCEPTED',0),
        signal_ready_returns=r['first_return_reasons'].get('AWAIT_CURRENT_TESTER_QUOTE_AND_STRATEGY_GUARDS',0),
        executed_entry_pairs=pair_count,executed_unique_setups=len(setups),
        setup_performance=performance(sum(v,D(0)) for v in setups.values()),
        position_performance=performance(D(p['net']) for p in positions),
        daily_entry_cohorts={day:performance(v) for day,v in sorted(daily.items())},
        native_report_metrics=r['native_report_metrics'],
        be_reconciled=be,protections_verified=len(positions),maximum_actual_open_lots=str(maximum),
        end_of_test_liquidations=sum(p['exit_comment']=='end of test' for p in positions),
        group_rejects=r['group_reasons'],return_rejects=r['first_return_reasons'],dispatch_results=r['dispatch_results'],
        setup_results=[dict(setup=k,net=str(sum(v,D(0))),positions=len(v)) for k,v in setups.items()],
        actual_positions=positions,
        costs='Actual Tester deal profit+commission+swap+fee; historical broker costs not independently certified.',
        statistical_warning='Small historical sample; identify training versus prespecified holdout separately. No Demo approval or claim of future profitability.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('results',nargs='+',type=Path)
    p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    rows=[analyze(r) for f in a.results for r in json.loads(f.read_text())]
    a.out.write_text(json.dumps(rows,indent=2))
    for r in rows:print(r['run'],r['setup_performance'],r['position_performance'])
