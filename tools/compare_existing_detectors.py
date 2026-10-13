"""Compare actual closed-bar diagnostics and an explicitly incomplete native prefix.

Never accepts an incomplete capture as loss-aware evidence or fabricates a summary.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.compare_native_retests import compare_rows
from traderlab.detection import Detector, Bar, instant
from traderlab.replay import digest

APPROVED=('BOS_CANDIDATE_QUALIFIED','BOS_CONFIRMED','BIG_CANDLE_CONFIRMED','FVG_CONFIRMED','OB_CONFIRMED')

def closed_signature(row):
    candidate=row.get('candidate_at')
    if candidate is None:
        candidate=datetime.fromtimestamp(row['candidate_server_epoch']-row['server_utc_offset_seconds'],timezone.utc)
    elif isinstance(candidate,str):
        candidate=instant(candidate)
    key=(row['event'],row['timeframe'],candidate,row.get('side'))
    value=(instant(row['time']) if 'time' in row else None,)+tuple(Decimal(str(x)) for x in row.get('zone',[]))
    if 'level' in row: value+=(Decimal(str(row['level'])),)
    if row['event']=='BIG_CANDLE_CONFIRMED': value+=(Decimal(str(row['body'])).quantize(Decimal('.00000001')),)
    if row['event']=='FVG_CONFIRMED': value+=(row['fill_state'],)
    if row['event']=='OB_CONFIRMED': value+=(row['anchor_candle'],instant(row['anchor_at']) if isinstance(row['anchor_at'],str) else row['anchor_at'])
    return key,value

def compare_closed(rows):
    detector=Detector(); native=Counter(); python=Counter(); bars=0; startup=0; first=None
    for row in rows:
        if row['event']=='CLOSED_BAR':
            bars+=1
            first=first or row['time']; startup+=row['time']==first
            for event in detector.accept(Bar.read(row)):
                if event['event'] in APPROVED: python[closed_signature({**event,'time':row['time']})]+=1
        elif row['event'] in APPROVED: native[closed_signature(row)]+=1
    delta=native-python; absent=python-native
    return {'scope':'legacy closed-bar accepted observations; no intrabar/execution parity claim',
            'bars':bars,'startup_history_bars':startup,'native_counts':dict(Counter(k[0][0] for k in native.elements())),
            'python_counts':dict(Counter(k[0][0] for k in python.elements())),
            'matches':native==python,'native_only':list(map(str,delta.elements()))[:20],
            'python_only':list(map(str,absent.elements()))[:20]}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--historical',required=True,type=Path)
    p.add_argument('--prefix',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    with a.historical.open(encoding='utf-8-sig') as f:
        historical=compare_closed(json.loads(line) for line in f if line.strip())
    # A finite byte snapshot is read once. Original capture remains untouched.
    data=a.prefix.read_bytes(); lines=data.splitlines(); truncated=False
    if data and not data.endswith(b'\n'):
        lines=lines[:-1]; truncated=True
    rows=[json.loads(line.decode('utf-8-sig')) for line in lines if line.strip()]
    config=json.loads((Path(__file__).resolve().parents[1]/'configs/production.template.json').read_text(encoding='utf-8'))
    prefix=compare_rows(rows,config,diagnostic_prefix=True,all_candidates=True)
    import hashlib
    prefix.update(snapshot_bytes=len(data),snapshot_sha256=hashlib.sha256(data).hexdigest(),truncated_last_line=truncated)
    report={'historical':{**historical,'sha256':digest(a.historical)},'native_live_prefix':prefix,
            'full_native_python_parity':'NOT_ESTABLISHED','new_core_controller_runtime':'REQUIRES_FRESH_MT5_RUN'}
    a.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2));return 0 if historical['matches'] and prefix['matches'] else 1

if __name__=='__main__':raise SystemExit(main())
