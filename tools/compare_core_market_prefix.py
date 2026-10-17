"""Prove each native study used the original ordered tick prefix, including duplicates."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.verify_auto_tick_history import record

def fingerprint(path, limit=None, bar_limit=None):
    h=hashlib.sha256();bars=hashlib.sha256();n=nb=0;first=last=None
    for line in path.open('rb'):
        if b'"event":"TICK"' in line and (limit is None or n<limit):
            r=json.loads(line);n+=1
            if r['tick_index']!=n:raise ValueError('Ordering/multiplicity changed')
            h.update(record(r['time_msc'],r['bid'],r['ask'],r['last'],r['volume']))
            h.update(f"{int(r['flags'])}|{float(r['volume_real']):.16f}\n".encode())
            first=first or r['server_time'];last=r['server_time']
        elif b'"event":"BOS_TRACKER_CLOSED_BAR"' in line and (bar_limit is None or nb<bar_limit):
            r=json.loads(line);nb+=1
            bars.update(('|'.join([r['timeframe'],r['opened_at']]+[f"{float(r[k]):.8f}" for k in ('open','high','low','close')])+'\n').encode())
        if n==limit and nb==bar_limit:break
    return {'ticks':n,'sha256':h.hexdigest(),'first_server':first,'last_server':last,
            'closed_bars':nb,'bar_ohlc_sha256':bars.hexdigest()}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('original',type=Path);p.add_argument('captures',nargs='+',type=Path)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args();refs={};results=[]
    for f in a.captures:
        actual=fingerprint(f);key=actual['ticks'],actual['closed_bars']
        if key not in refs:refs[key]=fingerprint(a.original,*key)
        if actual!=refs[key]:raise ValueError(f'Original market sequence differs: {f}')
        results.append({'capture':str(f),'identical_original_prefix':True,**actual})
    with a.out.open('x') as f:json.dump(results,f,indent=2)
    print(json.dumps(results,indent=2))
