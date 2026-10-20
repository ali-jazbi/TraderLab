"""Read-only §54 impact on genuine archived candles and frozen Native packages.

Never turns removed historical trades into a counterfactual PnL calculation.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from decimal import Decimal as D

from traderlab.detection import Bar, has_bos_wick
from traderlab.strategy import Bos, Zone, Unresolved, entry_reference, select_bos


def inspect(raw, start, end):
    digest=hashlib.sha256(); seeds={}; qualified={}; confirmed={}; groups={}
    rejected=Counter(); total=Counter(); gaps=hashlib.sha256(); step=None
    needles=(b'BROKER_CAPABILITY_SNAPSHOT',b'BOS_TRACKER_CLOSED_BAR',
             b'CORE_BOS_CANDIDATE_QUALIFIED',b'CORE_BOS_CONFIRMED',
             b'EXPERIMENTAL_GROUP_FINALIZED',b'CORE_FVG_CONFIRMED',b'CORE_OB_CONFIRMED')
    with Path(raw).open('rb') as source:
        for line in source:
            digest.update(line)
            if b'"event":"TICK"' in line or not any(n in line for n in needles):
                continue
            e=json.loads(line); event=e['event']
            if event=='BROKER_CAPABILITY_SNAPSHOT':
                step=str(e['tick_size']); continue
            if event=='BOS_TRACKER_CLOSED_BAR':
                if step is None: raise ValueError('Missing genuine broker price precision')
                b=Bar.read(e)
                for side in ('BUY','SELL'):
                    key=f'{b.timeframe}:{side}:{b.opened.isoformat()}'
                    allowed=has_bos_wick(b,side,step)
                    seeds[key]=dict(allowed=allowed,timeframe=b.timeframe)
                    if start<=e['server_time']<end:
                        total[b.timeframe]+=1
                        if not allowed: rejected[b.timeframe]+=1
            elif event=='CORE_BOS_CANDIDATE_QUALIFIED': qualified[e['bos_id']]=e
            elif event=='CORE_BOS_CONFIRMED': confirmed[e['bos_id']]=e
            elif event=='EXPERIMENTAL_GROUP_FINALIZED': groups[e['fvg_id']]=e
            elif event in ('CORE_FVG_CONFIRMED','CORE_OB_CONFIRMED'):
                # Exclude only log sequence; exact actual availability/geometry stay in the proof.
                gaps.update((json.dumps({k:v for k,v in e.items() if k!='seq'},sort_keys=True)+'\n').encode())
    def removed(events):
        return [key for key,e in events.items() if start<=e['server_time']<end
                and key in seeds and not seeds[key]['allowed']]
    missing=sorted(set(qualified)-set(seeds))
    return dict(raw_sha256=digest.hexdigest(),price_step=step,
                measured_seed_count_by_timeframe=dict(total),
                measured_no_wick_seeds_by_timeframe=dict(rejected),
                measured_qualified_removed_ids=removed(qualified),
                measured_confirmed_removed_ids=removed(confirmed),
                missing_ohlc_qualified_ids=missing,fvg_ob_sha256=gaps.hexdigest(),
                seeds=seeds,qualified=qualified,confirmed=confirmed,groups=groups)


def comparison(before, after, start, end):
    # The previous closed-bar qualification and break chronology must be
    # identical for every surviving seed. No silent new ranking or policy.
    expected={k:v for k,v in before['qualified'].items()
              if k not in before['seeds'] or before['seeds'][k]['allowed']}
    if set(expected)!=set(after['qualified']):
        raise ValueError('Qualification changed beyond the directional-shadow rule')
    for key,e in expected.items():
        if e['server_time']!=after['qualified'][key]['server_time']:
            raise ValueError('Surviving BOS qualification chronology changed')
    if before['fvg_ob_sha256']!=after['fvg_ob_sha256']:
        raise ValueError('FVG/OB detection or availability changed')
    changes=[]
    for key,old in before['groups'].items():
        if not start<=old['server_time']<end: continue
        new=after['groups'].get(key)
        if new is None: raise ValueError('Missing unchanged FVG group diagnostic')
        fields=('members','all_geometric_members','selected_bos_ids','accepted','reason','entry1','entry2')
        if any(old.get(k)!=new.get(k) for k in fields):
            changes.append(dict(fvg_id=key,server_time=old['server_time'],
                                before={k:old.get(k) for k in fields},
                                after={k:new.get(k) for k in fields}))
    return dict(packages_changed=len(changes),package_changes=changes,
                surviving_qualification_chronology_identical=True,fvg_ob_unchanged=True)


def project_groups(before, start, end):
    """As-of membership/selection only; no synthetic fills, costs or daily-state PnL."""
    changes=[]; missing=set()
    for key,old in before['groups'].items():
        if not start<=old['server_time']<end: continue
        members=[]; by_level={}
        for identity in filter(None,old['all_geometric_members'].split(';')):
            if identity not in before['seeds'] or identity not in before['qualified']:
                missing.add(identity);continue
            if not before['seeds'][identity]['allowed']: continue
            q=before['qualified'][identity];level=D(q['level'])
            # Same existing earliest-qualified equal-level tie-break, fixed as of availability.
            rank=(q['time'],identity.split(':',2)[2],identity)
            if level not in by_level:
                by_level[level]=(len(members),rank);members.append(identity)
            elif rank<by_level[level][1]:
                i,_=by_level[level];members[i]=identity;by_level[level]=(i,rank)
        selected=[]; reason=''
        if not members: reason='NO_QUALIFIED_CONTAINED_BOS_AT_CONFIRMATION'
        elif old['fill_at_confirmation']=='FULL': reason='FULL_OR_UNKNOWN_FVG_INVALID'
        else:
            side=key.split(':')[1]
            candidates=[]
            for identity in members:
                level=D(before['qualified'][identity]['level'])
                candidates.append(Bos(identity,entry_reference(side,level),Zone(level,level),level))
            try: selected=[b.id for b in select_bos(side,candidates)]
            except Unresolved as e: reason=str(e)
        previous=list(filter(None,old['selected_bos_ids'].split(';')))
        if members!=list(filter(None,old['members'].split(';'))) or set(selected)!=set(previous):
            changes.append(dict(fvg_id=key,server_time=old['server_time'],before_members=old['members'],
                                after_members=members,before_selected=previous,after_selected=selected,
                                before_accepted=old['accepted'],after_structural_reason=reason,
                                before_entry_count=len(previous),after_entry_count=len(selected)))
    return dict(scope='STRUCTURAL_PROJECTION_ONLY_NOT_NATIVE_TRADES_OR_COUNTERFACTUAL_PNL',
                groups_with_members_or_selection_changed=len(changes),
                groups_with_selection_changed=sum(set(c['before_selected'])!=set(c['after_selected']) for c in changes),
                previously_accepted_groups_changed=sum(c['before_accepted'] for c in changes),
                missing_ohlc_ids=sorted(missing),changes=changes)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,required=True)
    parser.add_argument('--start',required=True);parser.add_argument('--end',required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists(): raise ValueError('Refuse overwriting archived analysis')
    result=inspect(args.capture,args.start,args.end)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('seeds','qualified','confirmed','groups')}))
