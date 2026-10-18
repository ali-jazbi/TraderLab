"""Independent as-of membership audit of the named native studies; no fills/PnL."""
import argparse
from collections import Counter,defaultdict
from datetime import timedelta
from decimal import Decimal as D
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from traderlab.detection import instant,TIMEFRAMES
from traderlab.retests import FirstReturn
from traderlab.strategy import Bos, core_plan, entry_reference

NAMES={1:'FRESH_CONFIRMED',2:'IMPULSE_GLOBAL',3:'IMPULSE_ARMED'}

def captured_lines(path):
    with path.open('rb') as stream:
        yield from stream

def members(rows, mode, armed_consumed=()):
    selected=[]
    for r in rows:
        if r['bos_timeframe']!=r['fvg_timeframe'] or not r['qualified_at']:continue
        start=instant(r['fvg_candidate_at']);end=start+timedelta(seconds=TIMEFRAMES[r['fvg_timeframe']])
        if instant(r['qualified_at'])>instant(r['fvg_available_at']):continue
        if mode!=3 and r['first_return_consumed']:continue
        if mode>=2 and (not r['break_at'] or not start<=instant(r['break_at'])<end):continue
        if mode==3 and r['bos_id'] in armed_consumed:continue
        selected.append(r)
    selected.sort(key=lambda r:(instant(r['qualified_at']),instant(r['candidate_at']),r['bos_id']))
    unique={}
    for r in selected:unique.setdefault(D(r['bos_level']),r)
    return list(unique.values())

def audit(path,mode,server_from='2026-10-07',server_until='2026-10-10'):
    relations=defaultdict(dict);seen=set();n=0;plans=0;window=Counter();failures=[]
    for line in captured_lines(path):
        if not any(x in line for x in (b'"event":"CORE_SETUP_CANDIDATE"',b'"event":"EXPERIMENTAL_GROUP_FINALIZED"',b'"event":"EXPERIMENTAL_ARMED_FIRST_RETURN"')):continue
        r=json.loads(line)
        if r['event']=='CORE_SETUP_CANDIDATE':relations[r['fvg_id']][r['bos_id']]=r
        elif r['event']=='EXPERIMENTAL_ARMED_FIRST_RETURN':seen.add(r['bos_id'])
        else:
            selected=members(relations[r['fvg_id']].values(),mode,seen)
            expected={m['bos_id'] for m in selected}
            actual=set(filter(None,r['members'].split(';')));n+=1
            if expected!=actual:failures.append({'fvg':r['fvg_id'],'native_only':sorted(actual-expected),'python_only':sorted(expected-actual)})
            if r['accepted']:
                side=r['fvg_id'].split(':')[1]
                # Zone is unused by the arithmetic planner; never invent a BOS zone.
                bs=[Bos(m['bos_id'],entry_reference(side,D(m['bos_level'])),None,D(m['bos_level'])) for m in selected]
                plan=core_plan(side,bs,{})
                if {b.id for b in plan.entries}!=set(r['selected_bos_ids'].split(';')) or plan.entries[0].entry!=D(str(r['entry1'])) or (len(plan.entries)==2 and plan.entries[1].entry!=D(str(r['entry2']))):
                    raise ValueError('Native/Python selected extremes mismatch: '+r['fvg_id'])
                plans+=1
            if server_from<=r['server_time'][:10]<server_until:
                window[(r['server_time'][:10],r['reason'] or 'STRUCTURAL_VALID')]+=1
    if failures:raise ValueError(json.dumps(failures[:5]))
    return {'policy':NAMES[mode],'groups_checked_including_warmup':n,'all_memberships_match':True,
            'accepted_extreme_selections_checked':plans,
            'measured_server_window':[server_from,server_until],
            'window_counts':[{'day':d,'reason':r,'count':n} for (d,r),n in sorted(window.items())],
            'scope':'Independent membership calculation only. No Python trades or profitability.'}


def audit_armed_returns(path):
    """Replay genuine captured Bid ticks through Python's independent return reducer."""
    levels={};arms={};native={}
    for line in captured_lines(path):
        if not any(x in line for x in (b'"event":"CORE_SETUP_CANDIDATE"',b'"event":"EXPERIMENTAL_GROUP_FINALIZED"',b'"event":"EXPERIMENTAL_ARMED_FIRST_RETURN"')):continue
        r=json.loads(line)
        if r['event']=='CORE_SETUP_CANDIDATE':levels[r['bos_id']]=D(r['bos_level'])
        elif r['event']=='EXPERIMENTAL_ARMED_FIRST_RETURN':
            if r['bos_id'] in native:raise ValueError('Repeated native armed return')
            native[r['bos_id']]=r
        elif r['accepted']:
            for key in filter(None,r['selected_bos_ids'].split(';')):
                side=key.split(':')[1];entry=levels[key]+(D('.5') if side=='BUY' else D('-.5'))
                arms.setdefault(key,(r['tick_index'],FirstReturn(side,entry)))
    by_index=defaultdict(list)
    for key,(index,reducer) in arms.items():by_index[index].append((key,reducer))
    active={};checked=set()
    for line in captured_lines(path):
        if b'"event":"TICK"' not in line:continue
        r=json.loads(line);index=r['tick_index'];active.update(by_index.get(index,()))
        consumed=[]
        for key,reducer in active.items():
            found=reducer.advance(D(r['bid']),r['server_time'],index,index)
            if found is None:continue
            n=native.get(key)
            if n is None or n['tick_index']!=index or n['server_time']!=r['server_time'] or D(str(n['previous_quote']))!=found['previous_quote'] or D(str(n['observed_quote']))!=found['observed_quote']:
                raise ValueError('Native/Python armed return mismatch: '+key)
            checked.add(key);consumed.append(key)
        for key in consumed:del active[key]
    if checked!=set(native):raise ValueError('Native returns missing from independent replay')
    return dict(armed_bos=len(arms),returns_checked=len(checked),not_yet_returned=len(active),
                identical_first_return_tick_and_quotes=True,
                scope='Actual captured Bid chronology and independent Python return reducer; no Python fills.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('--mode',type=int,choices=NAMES,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--returns',action='store_true')
    p.add_argument('--server-from',default='2026-10-07');p.add_argument('--server-until',default='2026-10-10')
    a=p.parse_args();r=audit(a.capture,a.mode,a.server_from,a.server_until)
    if a.returns:
        if a.mode!=3:p.error('--returns applies only to IMPULSE_ARMED')
        r['return_parity']=audit_armed_returns(a.capture)
    a.out.write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
