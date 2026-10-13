"""Actionable Core candidate evidence. Reporting never promotes a setup."""
import csv
import json
from datetime import timedelta
from .detection import instant
from .replay import encode


def core_candidates(engine, server_offset=None, startup_delivery=None):
    rows=[]
    for event in engine.events:
        if event['event'] not in ('AUTO_SETUP_BLOCKED','CROSS_TIMEFRAME_RELATIONSHIP_BLOCKED'):
            continue
        gap=engine.automatic.gaps[event['fvg_id']]
        bos=engine.automatic.bos[event['bos_id']]
        history=engine.retests.snapshot(event['bos_id']) or {}
        lane=history.get('bid',{})
        returned=lane.get('returns',{}).get('bid')
        reasons=list(event['reasons'])
        if gap['fill_state']=='FULL' and 'FVG_FULL_FILL_INVALID' not in reasons:
            reasons.append('FVG_FULL_FILL_INVALID_AT_END')
        if returned:
            reasons.append('FIRST_RETURN_CONSUMED_NO_RETROACTIVE_APPROVAL')
            if not returned['exact_quote']:
                reasons.append('MISSED_EXACT_SIGNAL_QUOTE_NO_FILL')
        startup=bool(startup_delivery and bos['qualified_at']==startup_delivery)
        if startup: reasons.append('STARTUP_HISTORY_NOT_EXECUTION_PROOF')
        required=[]
        if any('FVG_FULL' in x or 'CONSUMED' in x or 'MISSED_EXACT' in x for x in reasons):
            required.append('This historical opportunity cannot be rearmed or filled retroactively; inspect a new candidate.')
        required.append('Owner evidence identifying this BOS/FVG/C3-or-C1 package, complete BOS member IDs and group finalization time.')
        if event['bos_timeframe']!=event['fvg_timeframe']:
            required.append('Owner evidence allowing these exact BOS/FVG timeframes and candle identities; no inferred ranking.')
        if gap['fill_state']=='PARTIAL' or event['fill_state']=='PARTIAL':
            required.append('Explicit partial-fill permission and exact invalidation threshold; §52 left this unanswered.')
        required.append('Before a new executable setup: sourced session/news coverage, actual broker/cost inputs and reviewed locked-gateway integration.')
        utc={'bos_candle':event['candidate_at'],'qualification':bos['qualified_at'],
             'fvg_c2':gap['candidate_at'],'fvg_formation':gap.get('formation_at'),
             'fvg_confirmation':gap['available_at'],'ob_candle':gap['ob_anchor_at'],
             'intrabar_break':lane.get('break_at'),'first_return':returned['first_return_at'] if returned else None}
        chart={key:(instant(value) if isinstance(value,str) else value)+timedelta(seconds=server_offset)
               if value is not None and server_offset is not None else None for key,value in utc.items()}
        rows.append(encode({'candidate_id':event['setup_id'],'bos_id':event['bos_id'],
             'fvg_id':event['fvg_id'],'ob_id':gap['id']+':'+('C3' if event['side']=='BUY' else 'C1'),
             'side':event['side'],'bos_timeframe':event['bos_timeframe'],'fvg_timeframe':event['fvg_timeframe'],
             'bos_level':event['bos_level'],'entry_reference':event['entry_reference'],
             'fvg':gap['zone'],'ob':gap['ob'],'fill_at_relationship':event['fill_state'],
             'fill_at_end':gap['fill_state'],'utc':utc,
             'server_wall_time':{key:value.replace(tzinfo=None).isoformat(timespec='milliseconds') if value else None for key,value in chart.items()},
             'server_offset_seconds':server_offset,'first_return':returned,
             'startup_history':startup,'fully_approved':False,'broker_execution_enabled':False,
             'reasons':list(dict.fromkeys(reasons)),'minimal_evidence':required}))
    return rows


def write_candidates(engine, output, server_offset=None, startup_delivery=None):
    rows=core_candidates(engine,server_offset,startup_delivery)
    (output/'core-candidates.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    fields=('candidate_id','bos_id','fvg_id','ob_id','side','bos_timeframe','fvg_timeframe',
            'bos_level','entry_reference','fill_at_relationship','fill_at_end','startup_history','reasons','minimal_evidence')
    with (output/'core-candidates.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields+('chart_times','fvg_prices','ob_prices','first_return'))
        writer.writeheader()
        for row in rows:
            writer.writerow({**{k:json.dumps(row[k],ensure_ascii=False) if isinstance(row[k],list) else row[k] for k in fields},
                             'chart_times':json.dumps(row['server_wall_time']),'fvg_prices':json.dumps(row['fvg']),
                             'ob_prices':json.dumps(row['ob']),'first_return':json.dumps(row['first_return'])})
    return len(rows)
