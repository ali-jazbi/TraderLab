"""Fixed Oct17 experimental gates over original as-of evidence; no fills/PnL."""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal as D
import json
from pathlib import Path

POLICIES = {1:'TOUCH_CROSSING',2:'NON_FULL_FVG',4:'PER_BOS_MEMBERSHIP'}

def compare(source):
    reports=[]
    for mask in range(8):
        counts=Counter(); candidates=[]; eligible=defaultdict(list)
        for g in source['groups']:
            for r in g['post_confirmation_returns']:
                if not r['selected_by_frozen_extremes']: continue
                reason=''
                selected=g['selected_at_confirmation']
                if len(g['selected_ids'])!=2: reason=g['structural_blocker'] or 'SINGLE_BE_ANCHOR_UNRESOLVED'
                elif any(s['startup'] for s in selected.values()): reason='STARTUP_HISTORY'
                elif selected[r['bos_id']]['consumed']: reason='THIS_BOS_ALREADY_CONSUMED'
                elif not mask&4 and any(s['consumed'] for s in selected.values()): reason='OTHER_SELECTED_BOS_CONSUMED'
                elif g['fill_at_confirmation']=='FULL' or r['fill_after_return_tick']=='FULL': reason='FULL_FVG'
                elif g['fill_at_confirmation'] not in ('UNFILLED','PARTIAL') or r['fill_after_return_tick'] not in ('UNFILLED','PARTIAL'): reason='UNKNOWN_FVG'
                elif not mask&2 and (g['fill_at_confirmation']!='UNFILLED' or r['fill_after_return_tick']!='UNFILLED'): reason='PARTIAL_FVG'
                elif not r['exact_quote']:
                    q=r['observed_tick']; ref=D(r['entry_reference']);bid=D(q['bid']);ask=D(q['ask']); buy=':BUY:' in r['bos_id']
                    if not mask&1: reason='EXACT_QUOTE_MISSED'
                    elif abs(bid-ref)>D('.5') or abs((ask if buy else bid)-ref)>D('.5'): reason='CROSSING_OVER_5_PIPS'
                if reason: counts[reason]+=1; continue
                eligible[(r['bos_id'],r['tick_index'])].append({'fvg_id':g['fvg_id'],
                    'confirmation':g['confirmation_server'],'fill_at_confirmation':g['fill_at_confirmation'],
                    'fvg':g['fvg'],'selected_ids':g['selected_ids'],**r})
        for rows in eligible.values():
            if len(rows)>1: counts['MULTIPLE_FVG_PACKAGES']+=len(rows)
            else: candidates.extend(rows)
        candidates.sort(key=lambda r:r['tick_index'])
        reports.append({'mask':mask,'policies':[name for bit,name in POLICIES.items() if mask&bit] or ['STRICT_BASELINE'],
                        'quote_candidates':candidates,'rejected_selected_returns':dict(counts)})
    return {'scope':'ANALYTICAL_GATES_ONLY_NOT_BROKER_ORDERS','source_sha256':source['sha256'],
            'ticks':source['ticks'],'crossing_max_strategy_pips':5,'variants':reports}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args(); report=compare(json.loads(a.source.read_text()))
    with a.out.open('x') as f:json.dump(report,f,indent=2)
    for r in report['variants']:
        print(r['mask'],len(r['quote_candidates']),r['rejected_selected_returns'])
        for c in r['quote_candidates']:print(' ',c['server_time'],c['bos_id'],c['entry_reference'],c['observed_tick']['bid'],c['observed_tick']['ask'])
