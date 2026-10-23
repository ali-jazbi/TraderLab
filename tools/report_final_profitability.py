"""Audit frozen Native runs; engineering success never grants profitability PASS."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal as D
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil

from tools.compare_core_market_prefix import fingerprint
from tools.report_body80_study import structural_proof
from tools.report_core_policy_runs import audit
from tools.report_discovery_study import analyze

CASES = {'W1_20261019_20': ('2026-10-19', '2026-10-21'),
         'W2_20261021_22': ('2026-10-21', '2026-10-23')}


class Rows(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows = []; self.row = []; self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr': self.row = []
        if tag in ('td', 'th'): self.cell = []

    def handle_data(self, data):
        if self.cell is not None: self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split())); self.cell = None
        if tag == 'tr' and self.row: self.rows.append(self.row)


def html_costs(path, expected_net):
    blob = path.read_bytes(); parser = Rows()
    parser.feed(blob.decode('utf-16' if blob[:2] in (b'\xff\xfe', b'\xfe\xff') else 'utf-8-sig'))
    header = None; deals = []
    for row in parser.rows:
        if all(s in row for s in ('Deal', 'Direction', 'Commission', 'Swap', 'Profit')):
            header = row; continue
        if header and len(row) == len(header) and re.fullmatch(r'\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}', row[0]):
            item = dict(zip(header, row))
            if item.get('Type') != 'balance': deals.append(item)
    if header is None: raise ValueError('Missing native deal cost table')
    value = lambda text: D(text.replace(' ', '').replace('\xa0', ''))
    total = lambda name: sum((value(d[name]) for d in deals), D(0))
    gross, commission, swap = (total(k) for k in ('Profit', 'Commission', 'Swap'))
    fee = total('Fee') if 'Fee' in header else None
    residual = D(str(expected_net)) - gross - commission - swap - (fee or D(0))
    if abs(residual) > D('.005'): raise ValueError('Native cost components do not reconcile with actual deal net')
    return dict(deal_rows=len(deals), gross_profit=str(gross), commission=str(commission),
                swap=str(swap), explicit_fee_column='Fee' in header,
                explicit_fee=str(fee) if fee is not None else None,
                unitemized_net_residual=str(residual), reconciled=True,
                spread='Embedded in actual Bid/Ask prices, not subtracted a second time',
                historical_broker_costs_independently_verified=False)


def sample_units(positions):
    """Diagnostic dependence grouping; never changes strategy membership or trades."""
    setups = {}
    for p in positions:
        s = setups.setdefault(p['setup'], dict(net=D(0), entries=[], exits=[], positions=0))
        s['net'] += D(p['net']); s['positions'] += 1
        s['entries'].append(datetime.fromisoformat(p['entry_time']))
        s['exits'].append(datetime.fromisoformat(p['exit_time']))
    keys = sorted(setups); parent = list(range(len(keys)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i

    for i, a in enumerate(keys):
        for j in range(i):
            b = keys[j]; x, y = setups[a], setups[b]
            overlap = max(min(x['entries']), min(y['entries'])) <= min(max(x['exits']), max(y['exits']))
            # FVG identity contains timeframe, direction and C2 open time.
            ax, bx = a.split(':', 3), b.split(':', 3)
            shared_impulse = len(ax) == len(bx) == 4 and ax[2:] == bx[2:]
            if overlap or shared_impulse: parent[find(i)] = find(j)
    clusters = {}
    for i, key in enumerate(keys): clusters.setdefault(find(i), []).append(key)
    return dict(position_legs=len(positions), unique_setups=len(keys),
                setup_returns=[dict(setup=k,net=str(setups[k]['net']),positions=setups[k]['positions']) for k in keys],
                overlap_or_shared_impulse_clusters=[dict(setups=v,net=str(sum((setups[k]['net'] for k in v),D(0)))) for v in clusters.values()],
                independent_sample_size_verified=None,
                note='Unique IDs or disjoint holding intervals do not establish statistical independence. Clusters are analysis only.')


def execution_observations(positions):
    rows = []
    for p in positions:
        q = p['actual_signal_quote']; side = p['side']
        quote = D(str(q['ask' if side == 1 else 'bid']))
        rows.append(dict(position=p['position'],entry_time=p['entry_time'],
                         spread_at_signal=str(D(str(q['ask']))-D(str(q['bid']))),
                         adverse_entry_fill_minus_quote=str(side*(D(p['entry'])-quote))))
    return dict(entries=rows, observed_entry_count=len(rows), tester_delay_ms=0,
                latency_tail_verified=False,slippage_tail_verified=False,
                note='Fill versus same-tick executable quote in zero-delay Tester; not a live execution guarantee.')


def runtime_inputs(folder, expected):
    values={}
    for path in (folder/'terminal/Tester').glob('Agent-*/logs/*.log'):
        b=path.read_bytes();encoding='utf-16' if b[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig'
        for line in b.decode(encoding,errors='replace').splitlines():
            match=re.search(r'\b(Inp\w+)=(.*)$',line)
            if match:values[match[1]]=match[2].strip()
    for key, original in expected.items():
        actual=values.get(key)
        if key=='InpTesterCoreExecutionFromServer':
            original=str(int(datetime.strptime(original,'%Y.%m.%d %H:%M:%S').replace(tzinfo=timezone.utc).timestamp()))
        if actual==original:continue
        try:
            if actual is not None and D(actual)==D(original):continue
        except Exception:
            pass
        raise ValueError('Native Agent did not confirm frozen input: '+key)
    return dict(checked_input_count=len(expected),all_match=True,agent_reported_inputs=values)


def verdict(windows, criteria, evidence):
    missing = [key for key, valid in evidence.items() if not valid]
    for key in ('maximum_drawdown', 'minimum_independent_setups', 'minimum_separate_windows'):
        if criteria.get(key) is None: missing.append('UNSET_'+key.upper())
    if not windows or any(w.get('independent_setup_count') in (None, 0) for w in windows):
        missing.append('INDEPENDENT_SAMPLE_EMPTY_OR_UNVERIFIED')
    if missing: return dict(status='INSUFFICIENT_EVIDENCE',reasons=sorted(set(missing)))
    if len(windows) < criteria['minimum_separate_windows'] or sum(w['independent_setup_count'] for w in windows) < criteria['minimum_independent_setups']:
        return dict(status='INSUFFICIENT_EVIDENCE',reasons=['PREREGISTERED_SAMPLE_MINIMUM_NOT_MET'])
    failures = []
    cap = criteria['maximum_drawdown']; unit = cap['unit']
    if unit not in ('usd', 'percent'): raise ValueError('Explicit drawdown unit required')
    for w in windows:
        if D(str(w['net'])) <= D(str(criteria['net_profit_gt'])): failures.append(w['name']+':NET_NOT_POSITIVE')
        if w['setup_profit_factor'] is None:
            if not w.get('positive_sample_without_losses', False): failures.append(w['name']+':PF_UNDEFINED')
        elif D(str(w['setup_profit_factor'])) <= D(str(criteria['profit_factor_gt'])): failures.append(w['name']+':PF_BELOW_OR_EQUAL_THRESHOLD')
        if D(str(w['drawdown_'+unit])) > D(str(cap['value'])): failures.append(w['name']+':DRAWDOWN_EXCEEDED')
    return dict(status='FAIL' if failures else 'PASS',reasons=failures)


def report(archive, out, frozen_path, calendar_manifest):
    frozen = json.loads(frozen_path.read_text()); cal = json.loads(calendar_manifest.read_text())
    sealed=json.loads((frozen_path.parent/'run-protocol.json').read_text())
    out.mkdir(parents=True,exist_ok=False); windows=[]; records=[]
    for name, (start, until) in CASES.items():
        folder=archive/name; target=out/name; target.mkdir()
        for f in folder.iterdir():
            if f.is_file() and f.suffix.lower() in ('.html','.png','.ini','.set','.json'): shutil.copy2(f,target/f.name)
        # Publish terminal/agent evidence; exclude Network-category authorization/IP lines.
        for f in (folder/'terminal').glob('**/logs/*.log'):
            dest=(target/f.relative_to(folder/'terminal')).with_suffix('.log.txt'); dest.parent.mkdir(parents=True,exist_ok=True)
            b=f.read_bytes(); enc='utf-16' if b[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig'
            text=f.read_text(encoding=enc,errors='replace')
            if f.parent.parent==folder/'terminal': text='\n'.join(s for s in text.splitlines() if '\tNetwork\t' not in s)+'\n'
            dest.write_text(text,encoding='utf-8')
        # Retain *all* outcomes diagnostically if the feed fails strict quality.
        # The failed quality gate prevents a final PASS; no losing run is omitted.
        r=audit(folder,start,until,strict_real_ticks=False); p=analyze(r)
        protocol=next(c for c in sealed['cases'] if c['case']==name)
        for path in (next(folder.glob('*.set')),next(folder.glob('*.ini')),folder/'tested.ex5',folder/'native-files/TraderLab-auto-tester-calendar.csv'):
            if hashlib.sha256(path.read_bytes()).hexdigest()!=protocol['hashes'][path.name]:raise ValueError('Sealed run file changed: '+path.name)
        if r['compiled_binary_sha256'] != frozen['tested_binary_sha256']: raise ValueError('Frozen binary changed')
        expected={k:v for k,v in frozen['parameters'].items() if k not in ('InpLogFile','InpTesterCoreExecutionFromServer')}
        actual={k:v for k,v in r['inputs'].items() if k not in ('InpLogFile','InpTesterCoreExecutionFromServer')}
        if actual!=expected or r['inputs']['InpTesterCoreExecutionFromServer']!=start.replace('-','.')+' 00:00:00': raise ValueError('Frozen strategy parameters changed')
        loaded=runtime_inputs(folder,r['inputs'])
        calendar=folder/'native-files/TraderLab-auto-tester-calendar.csv'
        if hashlib.sha256(calendar.read_bytes()).hexdigest()!=cal['sha256']: raise ValueError('Calendar changed')
        ini=next(folder.glob('*.ini')).read_text(encoding='utf-16')
        for line in ('Model=4','ExecutionMode=0','AllowLiveTrading=0','Optimization=0','FromDate=2026.09.21','ToDate='+until.replace('-','.')):
            if line not in ini.splitlines(): raise ValueError('Native test configuration changed: '+line)
        raw=next((folder/'native-files').glob('POL*.jsonl'))
        market=fingerprint(raw); structure=structural_proof(raw)
        costs=html_costs(next(folder.glob('*.html')),p['position_performance']['net'])
        units=sample_units(p['actual_positions']); execution=execution_observations(p['actual_positions'])
        if costs['deal_rows'] != sum(len(v) for v in r['positions'].values()): raise ValueError('Cost table/deal multiplicity changed')
        for filename, value in [('results',r),('performance',p),('market',market),('detection',structure),('runtime-inputs',loaded),('tick-quality',r['native_tick_quality']),('costs',costs),('sample',units),('execution',execution)]:
            (target/(filename+'.json')).write_text(json.dumps(value,indent=2)+'\n')
        percent=re.search(r'\(([\d.]+)%\)',p['native_report_metrics']['Equity Drawdown Maximal:'])
        event=next(e for e in r['events'] if e['event']=='TESTER_CORE_METRICS')
        s=p['setup_performance']
        windows.append(dict(name=name,net=s['net'],setup_profit_factor=s['net_unit_profit_factor'],
                            positive_sample_without_losses=s['count']>0 and s['wins']>0 and s['losses']==0,
                            unique_setup_count=units['unique_setups'],independent_setup_count=units['independent_sample_size_verified'],
                            overlap_cluster_count=len(units['overlap_or_shared_impulse_clusters']),
                            positions=p['position_performance']['count'],native_profit_factor=p['native_report_metrics'].get('Profit Factor:'),
                            drawdown_usd=event['max_equity_drawdown'],drawdown_percent=percent.group(1) if percent else None,
                            end_of_test_liquidations=p['end_of_test_liquidations']))
        records.append(dict(name=name,archive=str(folder),capture_and_native_deals_verified=True,
                            real_ticks_only_verified=r['native_tick_quality']['real_ticks_only_verified'],
                            generated_tick_fallback_minutes=r['native_tick_quality']['maximum_reported_missing_minutes'],
                            compiled_binary_sha256=r['compiled_binary_sha256'],raw_sha256=r['raw_sha256'],
                            measured_ticks=r['measured_ticks'],warmup_ticks=r['warmup_ticks'],
                            net_after_tester_costs=s['net'],historical_broker_costs_verified=False))
    evidence=dict(complete_native_capture_and_deals=True,all_ticks_real_including_warmup=all(r['real_ticks_only_verified'] for r in records),proven_independent_final_sample=False,
                  historical_all_in_costs_verified=False,latency_and_slippage_distribution_verified=False,
                  historical_calendar_asof_verified=cal['historical_asof_availability_proved'])
    result=dict(**verdict(windows,frozen['acceptance'],evidence),baseline_commit=frozen['baseline_commit'],
                frozen_manifest_sha256=hashlib.sha256(frozen_path.read_bytes()).hexdigest(),
                criteria=frozen['acceptance'],evidence=evidence,windows=windows,runs=records,
                policy='No dropped losing trades, no outcome-based changes, unique setups/overlap clusters distinct from statistical independence.',
                implementation_corrections=[],demo_scope='Forward evaluation only; dispatch remains locked',real_enabled=False)
    (out/'assessment.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('archive',type=Path); cli.add_argument('--out',type=Path,required=True)
    cli.add_argument('--frozen',type=Path,default=Path('docs/reports/final-profitability-20261023/frozen-version.json'))
    cli.add_argument('--calendar-manifest',type=Path,default=Path('docs/reports/final-profitability-20261023/candidate-calendar.manifest.json'))
    args=cli.parse_args(); result=report(args.archive,args.out,args.frozen,args.calendar_manifest)
    print(json.dumps(dict(status=result['status'],windows=result['windows'],reasons=result['reasons']),indent=2))
