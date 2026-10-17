"""Read original captures without replaying or inventing orders.

Freeze same-frame groups from the recorded as-of membership and compare only the
already authorized equal-level and FIRST_TOUCH hypotheses. Noneligible returns
remain diagnostic; this tool never creates a trade or measures profitability.
"""
import argparse
from collections import Counter
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from traderlab.strategy import Bos, Zone, core_plan, Unresolved
from traderlab.replay import encode


def trace(path):
    with path.open('rb') as stream:
        return trace_stream(path,stream)


def trace_stream(path,stream):
    config=json.loads((Path(__file__).resolve().parents[1]/'configs/production.template.json').read_text())
    digest=hashlib.sha256(); relations={}; returned={}; groups={}; fills={}; before={}; tick=-1
    reasons=Counter(); original=Counter(); pending={}; member_returns=[]; summary=None; capture=None; ticks_seen=0; last_tick=None
    for raw in stream:
        digest.update(raw)
        if b'"event":"TICK"' in raw:
            ticks_seen+=1
            last_tick=raw
            continue
        if not any(s in raw for s in (b'CORE_SETUP_CANDIDATE',b'EXPERIMENTAL_GROUP_FINALIZED',
                b'BOS_FIRST_DIRECTIONAL_RETURN',b'CORE_FVG_VALIDITY_CHANGED',b'CORE_CONTROLLER_SUMMARY',b'TICK_CAPTURE_SUMMARY')):continue
        r=json.loads(raw); event=r['event']; idx=r.get('tick_index',tick)
        if idx!=tick: tick=idx;before={}
        if event=='CORE_SETUP_CANDIDATE':
            relations[(r['fvg_id'],r['bos_id'])]=r
            fills.setdefault(r['fvg_id'],r['fill_state'])
        elif event=='CORE_FVG_VALIDITY_CHANGED':
            key=r['fvg_id']
            if r.get('source')=='observed_bid':before.setdefault(key,fills.get(key,'UNKNOWN'))
            fills[key]=r['fill_state']
        elif event=='EXPERIMENTAL_GROUP_FINALIZED':
            original[r['reason'] or 'ACCEPTED']+=1
            members=[relations[(r['fvg_id'],b)] for b in r['members'].split(';') if b]
            if any(not b['qualified_at'] or b['qualified_at']>b['fvg_available_at'] for b in members):
                raise ValueError('Recorded membership qualification is not proven as-of FVG availability')
            members.sort(key=lambda b:(b['qualified_at'] or '',b['candidate_at'],b['bos_id']))
            unique={}
            for b in members:unique.setdefault(D(b['bos_level']),b)
            members=list(unique.values()); reason=''; plan=None
            if not members:reason='NO_QUALIFIED_CONTAINED_BOS_AT_CONFIRMATION'
            else:
                try:
                    plan=core_plan(members[0]['side'],[Bos(b['bos_id'],D(b['entry_reference']),Zone(D(b['bos_level']),D(b['bos_level'])),D(b['bos_level'])) for b in members],config)
                    if len(plan.entries)==1:reason='SINGLE_BE_ANCHOR_UNRESOLVED'
                    for b in (plan.entries if not reason else []):
                        rel=next(m for m in members if m['bos_id']==b.id)
                        if rel['startup_history']:reason='STARTUP_HISTORY_NOT_EXECUTION_PROOF'
                        elif b.id in returned or rel['first_return_consumed']:reason='FIRST_RETURN_CONSUMED_BEFORE_GROUP_ACTIVATION'
                except Unresolved as e:reason=str(e)
            state=members[0]['fill_state'] if members else fills.get(r['fvg_id'],'UNKNOWN')
            # Original membership is frozen as-of. Native group first reasons carry
            # authoritative fill at confirmation, even if a relation was logged earlier.
            if r['reason']=='PARTIAL_NOT_APPROVED':state='PARTIAL'
            elif r['reason']=='FULL_OR_UNKNOWN_FVG_INVALID':state='FULL'
            row={'fvg_id':r['fvg_id'],'confirmation_server':r['server_time'],'confirmation_utc':r['time'],
                 'confirmation_tick':r['tick_index'],'fill_at_confirmation':state,
                 'original_reason':r['reason'] or 'ACCEPTED','structural_blocker':reason,
                 'selected_ids':[b.id for b in plan.entries] if plan else [],
                 'all_member_ids':[b['bos_id'] for b in members],
                 'selected_entries':[str(b.entry) for b in plan.entries] if plan else [],
                 'fvg':members[0]['fvg'] if members else None,'ob':members[0]['ob'] if members else None,
                 'policy':'EXPERIMENTAL_same_frame_earliest_qualified_equal_level_v1',
                 'post_confirmation_returns':[]}
            groups[r['fvg_id']]=row
            final_reason=reason or ('PARTIAL_AT_CONFIRMATION' if state=='PARTIAL' else 'FULL_AT_CONFIRMATION' if state=='FULL' else 'ACCEPTED_GEOMETRY')
            reasons[final_reason]+=1
            for b in members:pending.setdefault(b['bos_id'],[]).append(row)
        elif event=='BOS_FIRST_DIRECTIONAL_RETURN' and r['break_quote']=='bid' and r['retest_quote']=='bid':
            returned.setdefault(r['bos_id'],r)
            for g in pending.get(r['bos_id'],[]):
                # Closed bars/group are processed before the quote on this same tick.
                if r['tick_index']<g['confirmation_tick']:continue
                quote=json.loads(last_tick) if last_tick else None
                if not quote or quote['tick_index']!=r['tick_index'] or D(quote['bid'])!=D(r['observed_quote']):
                    raise ValueError('Return evidence does not match an actually captured Bid quote')
                if bool(r['exact_quote'])!=(D(r['observed_quote'])==D(r['entry_reference'])):
                    raise ValueError('Exact-return label contradicts observed price')
                f=g['fvg_id']; prior=before.get(f,fills.get(f,'UNKNOWN'));after=fills.get(f,'UNKNOWN')
                is_selected=r['bos_id'] in g['selected_ids']
                valid_structure=not g['structural_blocker'] and is_selected
                strict=valid_structure and g['fill_at_confirmation']=='UNFILLED' and after=='UNFILLED' and r['exact_quote']
                first=valid_structure and g['fill_at_confirmation']=='UNFILLED' and prior=='UNFILLED' and after!='FULL' and r['exact_quote']
                item={**{k:r[k] for k in ('bos_id','server_time','time','tick_index','entry_reference','previous_quote','observed_quote','exact_quote')},
                      'selected_by_frozen_extremes':is_selected,
                      'observed_tick':{k:quote[k] for k in ('tick_index','time','server_time','bid','ask','time_msc') if k in quote},
                      'fill_before_return_tick':prior,'fill_after_return_tick':after,
                      'strict_fvg_gate':bool(strict),'first_touch_fvg_gate':bool(first)}
                g['post_confirmation_returns'].append(item);member_returns.append({'fvg_id':f,**item})
        elif event=='CORE_CONTROLLER_SUMMARY':summary=r
        elif event=='TICK_CAPTURE_SUMMARY':capture=r
    if not summary or not capture or summary['controller_halted'] or capture['capture_halted'] or not capture['terminal_cursor_evidence_valid']:
        raise ValueError('Complete nonhalted original capture required')
    if summary.get('tester_experiment')!=1:
        raise ValueError('This comparison requires the original same-frame baseline, not a different grouping policy')
    if summary['processed_ticks']!=capture['emitted_ticks'] or ticks_seen!=capture['emitted_ticks']:raise ValueError('Tick counts do not reconcile')
    return {'scope':'DIAGNOSTIC_ONLY_NOT_ORDERS_OR_PERFORMANCE','capture':str(path),'sha256':digest.hexdigest(),
            'ticks':capture['emitted_ticks'],'controller':summary,'original_group_reasons':dict(original),
            'deduplicated_geometry_reasons':dict(reasons),'groups':list(groups.values()),
            'member_post_confirmation_returns':member_returns,
            'selected_post_confirmation_returns':[r for r in member_returns if r['selected_by_frozen_extremes']],
            'strict_fvg_gate_returns':sum(r['strict_fvg_gate'] for r in member_returns),
            'first_touch_fvg_gate_returns':sum(r['first_touch_fvg_gate'] for r in member_returns)}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); report=trace(a.capture)
    with a.out.open('x',encoding='utf8') as f:json.dump(encode(report),f,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k not in ('groups','selected_post_confirmation_returns','member_post_confirmation_returns','controller')},indent=2))
