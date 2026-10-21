"""Reconcile fresh Native Body80 runs; unavailable runs never become zero-profit results."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil

from tools.compare_core_market_prefix import fingerprint
from tools.report_core_policy_runs import audit
from tools.report_discovery_study import analyze

MODES=('BASELINE','BODY80','BODY80_AGE120')


def structural_proof(raw):
    h=hashlib.sha256();counts=Counter();eligibility=Counter();eligible_ids=set();locks=[]
    names={b'CORE_FVG_CONFIRMED',b'CORE_OB_CONFIRMED',b'CORE_BOS_CANDIDATE_QUALIFIED',
           b'CORE_BOS_CONFIRMED',b'CORE_BOS_REJECTED',b'CORE_FVG_VALIDITY_CHANGED',
           b'BOS_INTRABAR_BREAK',b'BOS_FIRST_DIRECTIONAL_RETURN'}
    for line in raw.open('rb'):
        if b'"event":"TICK"' in line:continue
        if b'"event":"CORE_SETUP_ELIGIBILITY"' in line:
            e=json.loads(line);eligibility['PASS' if e['eligible'] else 'REJECT']+=1
            if e['eligible']:eligible_ids.add(e['fvg_id'])
        elif b'"event":"CORE_LOCK_STATUS"' in line:
            e=json.loads(line);locks.append(e)
            # MT5 Tester exposes trade permission for simulated orders even
            # with terminal AllowLiveTrading=0. Never relabel that as Demo unlock.
            if not e['dispatch_locked'] or e['execution_requested']:
                raise ValueError('Demo lock evidence changed')
        elif any(b'"event":"'+n+b'"' in line for n in names):
            e=json.loads(line);counts[e['event']]+=1
            # Added OHLC evidence and log sequence are the only detector fields changed.
            e.pop('seq',None);e.pop('c2_ohlc',None)
            h.update((json.dumps(e,sort_keys=True,separators=(',',':'))+'\n').encode())
    if not locks:raise ValueError('Missing Demo lock runtime evidence')
    return dict(detection_sha256=h.hexdigest(),counts=dict(counts),eligibility=dict(eligibility),
                eligible_fvg_ids=sorted(eligible_ids),lock_evidence=locks)


def entry_identity(p):
    # Identity independent of run names, MT5 ticket allocation and later outcomes.
    return p['setup'],p['planned'],p['leg'],p['entry_time'],p['side']


def compare(before,after):
    a={entry_identity(p):p for p in before['actual_positions']}
    b={entry_identity(p):p for p in after['actual_positions']}
    return dict(removed=[a[k] for k in sorted(a.keys()-b.keys())],
                added=[b[k] for k in sorted(b.keys()-a.keys())],
                same_entry_count=len(a.keys()&b.keys()),
                note='Actual newly executed Tester deals in each run; no subtraction-based PnL estimate.')


def report(archive,out,baseline_archive=None):
    out.mkdir(parents=True,exist_ok=True);rows=[];results={};performances={};market={};structures={}
    for window in ('training','holdout'):
        start,end=('2026-10-07','2026-10-10') if window=='training' else ('2026-10-14','2026-10-17')
        for mode in MODES:
            name=window+'-'+mode;folder=(baseline_archive if mode=='BASELINE' and baseline_archive else archive)/name;target=out/name;target.mkdir(exist_ok=False)
            status=json.loads((folder/'run-status.json').read_text(encoding='utf-8-sig'))
            for f in folder.iterdir():
                if f.suffix.lower() in ('.html','.png','.set','.ini','.json'):shutil.copy2(f,target/f.name)
            logs=[]
            for f in (folder/'terminal').glob('**/logs/*.log'):
                # Retain actual terminal/agent startup and completion evidence, including failures.
                relative=f.relative_to(folder/'terminal');dest=(target/relative).with_suffix('.log.txt')
                dest.parent.mkdir(parents=True,exist_ok=True)
                if relative.parts[0]=='logs':
                    # Full local archive survives. Published evidence does not
                    # need account authorization/IP lines from the Network tab.
                    blob=f.read_bytes();encoding='utf-16' if blob[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig'
                    lines=f.read_text(encoding=encoding,errors='replace').splitlines()
                    dest.write_text('\n'.join(s for s in lines if '\tNetwork\t' not in s)+'\n',encoding='utf-8')
                else:shutil.copy2(f,dest)
                logs.append(str(dest.relative_to(target)))
            base=dict(window=window,mode=mode,archive=str(folder),status=status['status'],logs=logs,
                      ex5_sha256=hashlib.sha256((folder/'tested.ex5').read_bytes()).hexdigest())
            if not list(folder.glob('*.html')):
                rows.append(dict(base,validated=False,performance=None,reason='No completed real-tick Strategy Tester report. No outcome inferred.'))
                continue
            try:
                r=audit(folder,start,end);p=analyze(r)
                raw=next((folder/'native-files').glob('POL*.jsonl'))
                m=fingerprint(raw);s=structural_proof(raw)
                age=120 if mode=='BODY80_AGE120' else 0
                if int(r['inputs']['InpExperimentalM1MaxAgeMinutes'])!=age:raise ValueError('Wrong age mode')
                current={k:v for k,v in r['inputs'].items() if k not in ('InpLogFile','InpExperimentalM1MaxAgeMinutes')}
                calendar=(folder/'native-files/TraderLab-auto-tester-calendar.csv').read_bytes()
                if window in results:
                    ref=results[window]
                    expected={k:v for k,v in ref['inputs'].items() if k not in ('InpLogFile','InpExperimentalM1MaxAgeMinutes')}
                    if current!=expected:raise ValueError('Non-study execution input changed')
                    if m!=market[window]:raise ValueError('Ordered real ticks/closed bars differ between modes')
                    if calendar!=(Path(ref['archive'])/'native-files/TraderLab-auto-tester-calendar.csv').read_bytes():raise ValueError('Calendar changed')
                    if s['detection_sha256']!=structures[window]['detection_sha256']:raise ValueError('Detection history changed')
                else:
                    if mode!='BASELINE':raise ValueError('Missing fresh baseline')
                    results[window]=r;market[window]=m;structures[window]=s
                if mode!='BASELINE':
                    submitted=[e for e in r['events'] if e['event']=='CORE_TESTER_DISPATCH_RESULT' and e['submitted']]
                    for e in submitted:
                        group=e['frozen_group']
                        if group['reason']:raise ValueError('Rejected package dispatched')
                        if group['fvg_id'] not in s['eligible_fvg_ids']:raise ValueError('Package bypassed Core eligibility')
                (target/'results.json').write_text(json.dumps(r,indent=2)+'\n')
                (target/'performance.json').write_text(json.dumps(p,indent=2)+'\n')
                (target/'market.json').write_text(json.dumps(m,indent=2)+'\n')
                (target/'detection.json').write_text(json.dumps(s,indent=2)+'\n')
                performances[(window,mode)]=p
                rows.append(dict(base,validated=True,performance=p,market_identical_to_fresh_baseline=True,detection=s,
                                 calendar_sha256=hashlib.sha256(calendar).hexdigest()))
            except (ValueError,StopIteration,KeyError) as error:
                rows.append(dict(base,validated=False,performance=None,reason=str(error)))
    differences={}
    for window in ('training','holdout'):
        for mode in MODES[1:]:
            if (window,'BASELINE') in performances and (window,mode) in performances:
                differences[window+'-'+mode]=compare(performances[(window,'BASELINE')],performances[(window,mode)])
    result=dict(runs=rows,actual_trade_differences=differences,
                study='Fixed FRESH_CONFIRMED/mask7 settings; Sept21 warm-up; baseline main d460585 vs Body80 vs Body80+M1 AGE120. No tuning.',
                owner_m15_example=dict(exact_date=None,exact_feed=None,ohlc_identified=False,order_or_tp_sl_outcome=None,
                                       reason='Undated approximate educational image; no unique historical identification.'))
    (out/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);p.add_argument('--out',required=True,type=Path)
    p.add_argument('--baseline-archive',type=Path);a=p.parse_args()
    r=report(a.archive,a.out,a.baseline_archive)
    for row in r['runs']:print(row['window'],row['mode'],row['validated'],row.get('reason',''))
