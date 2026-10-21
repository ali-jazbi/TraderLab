"""Read-only §55 census on genuine capture; no fills, outcomes or PnL inference."""
import argparse
from collections import Counter
from decimal import Decimal as D
import hashlib
import gzip
import json
from pathlib import Path

from traderlab.core_eligibility import core_eligibility
from traderlab.detection import Bar, TIMEFRAMES, has_bos_wick, instant


def inspect(raw, expected_sha256=None):
    bars={};qualified={};rows=[];digest=hashlib.sha256();step=None;missing=set()
    with Path(raw).open('rb') as source:
        for line in source:
            digest.update(line)
            if b'"event":"TICK"' in line or not any(x in line for x in
                (b'BROKER_CAPABILITY_SNAPSHOT',b'BOS_TRACKER_CLOSED_BAR',b'CORE_BOS_CANDIDATE_QUALIFIED',b'CORE_FVG_CONFIRMED')):
                continue
            e=json.loads(line);event=e['event']
            if event=='BROKER_CAPABILITY_SNAPSHOT':
                step=D(str(e['tick_size']));continue
            if event=='BOS_TRACKER_CLOSED_BAR':
                b=Bar.read(e);bars[(b.timeframe,int(b.opened.timestamp()))]=b;continue
            if event=='CORE_BOS_CANDIDATE_QUALIFIED':
                tf,side,at=e['bos_id'].split(':',2);opened=instant(at)
                b=bars.get((tf,int(opened.timestamp())))
                if not b:missing.add(e['bos_id']);continue
                if step is None:raise ValueError('Missing broker tick grid')
                if has_bos_wick(b,side,step):
                    qualified[e['bos_id']]=dict(id=e['bos_id'],candidate_at=opened,
                        qualified_at=instant(e['time']),side=side,level=D(e['level']),timeframe=tf)
                continue
            tf=e['timeframe'];at=instant(e['candidate_at']);b=bars.get((tf,int(at.timestamp())))
            if b is None:raise ValueError('Missing real C2 OHLC')
            gap=dict(side=e['side'],candidate_at=at,available_at=instant(e['time']),
                     c2_ohlc={k:getattr(b,k) for k in ('open','high','low','close')},zone=list(map(D,e['zone'])))
            evidence=[q for q in qualified.values() if q['timeframe']==tf]
            eligibility=core_eligibility(gap,evidence)
            prior=[q for q in evidence if q['side']==gap['side'] and q['candidate_at']<at]
            # Only as-of confirmation state. No later tick, return, TP or SL is read.
            witnesses=[dict(q,level=str(q['level'])) for q in evidence if q['id'] in eligibility.witness_ids]
            rows.append(dict(fvg_id=f'{tf}:{gap["side"]}:{at.isoformat()}',
                timeframe=tf,side=gap['side'],candidate_at=at,available_at=gap['available_at'],
                server_available_at=e['server_time'],zone=gap['zone'],c2_ohlc=gap['c2_ohlc'],
                body_pips=eligibility.body_pips,has_valid_prior_bos=bool(prior),
                core_eligibility=eligibility.eligible,reasons=eligibility.reasons,
                fill_at_confirmation=e['fill_state'],
                non_full_eligible=eligibility.eligible and e['fill_state']!='FULL',
                strict_unfilled_eligible=eligibility.eligible and e['fill_state']=='UNFILLED',
                witnesses=witnesses))
    actual=digest.hexdigest()
    if expected_sha256 and actual!=expected_sha256:raise ValueError('Archive digest mismatch')
    if missing:raise ValueError('Qualified BOS has no real seed OHLC: '+str(sorted(missing)))
    if len({r['fvg_id'] for r in rows})!=len(rows):raise ValueError('Duplicate detected FVGs')
    return dict(raw=str(raw),raw_sha256=actual,tick_size=str(step),rows=rows,
                scope='Confirmed Big-Candle FVGs; all five frames; same-frame association only. '
                      'Historical §54 wick predicate reapplied to original qualified seeds; no trade simulation.')


def summarize(rows,start=None,end=None):
    if start:rows=[r for r in rows if start<=r['server_available_at']<end]
    result={}
    for tf in TIMEFRAMES:
        values=[r for r in rows if r['timeframe']==tf]
        result[tf]=dict(total_fvgs=len(values),body_ge_80=sum(r['body_pips']>=80 for r in values),
            valid_prior_bos=sum(r['has_valid_prior_bos'] for r in values),
            valid_prior_contained_bos=sum(bool(r['witnesses']) for r in values),
            body80_and_valid_prior=sum(r['body_pips']>=80 and r['has_valid_prior_bos'] for r in values),
            new_filter_pass=sum(r['core_eligibility'] for r in values),
            new_filter_non_full=sum(r['non_full_eligible'] for r in values),
            new_filter_strict_unfilled=sum(r['strict_unfilled_eligible'] for r in values),
            previous_non_full=sum(r['fill_at_confirmation']!='FULL' for r in values),
            previous_strict_unfilled=sum(r['fill_at_confirmation']=='UNFILLED' for r in values),
            rejection_reasons=dict(Counter(reason for r in values for reason in r['reasons'])))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',required=True,type=Path)
    p.add_argument('--sha256',required=True);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False);r=inspect(a.raw,a.sha256)
    r['statistics']={name:summarize(r['rows'],*window) for name,window in
        {'entire_archive':(None,None),'oct07_09':('2026-10-07','2026-10-10'),'oct14_16':('2026-10-14','2026-10-17')}.items()}
    examples=[x for x in r['rows'] if x['strict_unfilled_eligible'] and
              ('2026-10-07'<=x['server_available_at']<'2026-10-10' or '2026-10-14'<=x['server_available_at']<'2026-10-17')]
    examples.sort(key=lambda x:(x['available_at'],x['fvg_id']))
    # First five chronologically, independent of every subsequent result.
    (a.out/'examples.json').write_text(json.dumps(examples[:5],default=str,indent=2)+'\n',encoding='utf-8')
    with (a.out/'fvg-eligibility.json.gz').open('wb') as f:
        f.write(gzip.compress((json.dumps(r,default=str,indent=2)+'\n').encode(),mtime=0))
    (a.out/'statistics.json').write_text(json.dumps(r['statistics'],default=str,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r['statistics'],indent=2))
