"""Retain native HTML/deals and report actual Tester performance, never paper fills."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil

class Cells(HTMLParser):
    def __init__(self):super().__init__();self.active=False;self.buf=[];self.cells=[]
    def handle_starttag(self,tag,attrs):
        if tag=='td':self.active=True;self.buf=[]
    def handle_data(self,data):
        if self.active:self.buf.append(data)
    def handle_endtag(self,tag):
        if tag=='td' and self.active:self.cells.append(' '.join(''.join(self.buf).split()));self.active=False

def audit(folder):
    report=next(folder.glob('*.html')); blob=report.read_bytes(); cells=Cells()
    cells.feed(blob.decode('utf-16' if blob[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig'))
    labels=['History Quality:','Bars:','Ticks:','Total Trades:','Total Deals:','Total Net Profit:',
            'Gross Profit:','Gross Loss:','Profit Factor:','Equity Drawdown Maximal:',
            'Profit Trades (% of total):','Loss Trades (% of total):']
    metrics={k:cells.cells[cells.cells.index(k)+1] for k in labels if k in cells.cells}
    if metrics.get('History Quality:')!='100% real ticks':raise ValueError('Real-tick quality missing')
    raw=next((folder/'native-files').glob('POL*.jsonl')); digest=hashlib.sha256()
    events=[];groups=Counter();returns=Counter();dispatch=Counter();ticks=0;last_tick=None;frozen={}
    for line in raw.open('rb'):
        digest.update(line)
        if b'"event":"TICK"' in line:ticks+=1;last_tick=line;continue
        if not any(s in line for s in (b'TESTER_CORE_',b'CORE_CONTROLLER_SUMMARY',b'TICK_CAPTURE_SUMMARY',
                b'EXPERIMENTAL_GROUP_FINALIZED',b'EXPERIMENTAL_FIRST_RETURN',b'CORE_TESTER_DISPATCH_RESULT')):continue
        r=json.loads(line);kind=r['event']
        if kind=='EXPERIMENTAL_GROUP_FINALIZED':
            groups[r['reason'] or 'ACCEPTED']+=1;frozen[r['fvg_id']]=r
        elif kind=='EXPERIMENTAL_FIRST_RETURN':returns[r['reason']]+=1
        else:
            events.append(r)
            if kind=='CORE_TESTER_DISPATCH_RESULT':
                dispatch[r['reason'] or 'SUBMITTED']+=1
                q=json.loads(last_tick)
                if q['tick_index']!=r['tick_index']:raise ValueError('Dispatch evidence is not on the observed tick')
                r['actual_signal_quote']={k:q[k] for k in ['bid','ask','time_msc','tick_index','server_time']}
                r['frozen_group']=frozen[r['setup_id'].removeprefix('EXPERIMENTAL:')]
    capture=next(r for r in events if r['event']=='TICK_CAPTURE_SUMMARY')
    if capture['capture_halted'] or ticks!=capture['emitted_ticks'] or not capture['terminal_cursor_evidence_valid']:
        raise ValueError('Halted/incomplete market capture')
    positions={}
    for d in [r for r in events if r['event']=='TESTER_CORE_DEAL']:
        d['actual_server_time']=datetime.fromtimestamp(d['deal_time_msc']/1000,timezone.utc).isoformat().removesuffix('+00:00')
        positions.setdefault(d['position'],[]).append(d)
    native=next(r for r in events if r['event']=='TESTER_CORE_METRICS')
    entries=sum(d['entry_kind']==0 for rows in positions.values() for d in rows)
    closed=sum(any(d['entry_kind']==1 for d in rows) for rows in positions.values())
    if closed!=native['trades'] or closed!=int(metrics['Total Trades:']):raise ValueError('Closed positions do not reconcile')
    actual_net=sum((Decimal(str(d['net'])) for rows in positions.values() for d in rows),Decimal(0))
    if abs(actual_net-Decimal(metrics['Total Net Profit:'].replace(' ','')))>Decimal('.005'):raise ValueError('Deal costs/PnL do not reconcile')
    preset=next(folder.glob('*.set')).read_text(encoding='utf-16')
    inputs=dict(line.split('=',1) for line in preset.splitlines() if '=' in line)
    return {'run':folder.parent.name+'/'+folder.name,'archive':str(folder),'raw_sha256':digest.hexdigest(),
        'compiled_binary_sha256':hashlib.sha256((folder/'tested.ex5').read_bytes()).hexdigest(),
        'raw_bytes':raw.stat().st_size,'native_report_sha256':hashlib.sha256(blob).hexdigest(),
        'native_report_metrics':metrics,'ticks':ticks,'group_reasons':dict(groups),'first_return_reasons':dict(returns),
        'dispatch_results':dict(dispatch),'inputs':inputs,'actual_entry_deals':entries,'actual_closed_positions':closed,
        'deal_net_reconciled':str(actual_net),'events':events,'positions':positions}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folders',nargs='+',type=Path);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);results=[]
    for folder in a.folders:
        r=audit(folder);results.append(r);target=a.out/(folder.parent.name+'-'+folder.name);target.mkdir()
        for f in folder.iterdir():
            if f.suffix.lower() in ('.html','.png','.set','.ini'):shutil.copy2(f,target/f.name)
        print(r['run'],r['native_report_metrics'],r['dispatch_results'])
    (a.out/'results.json').write_text(json.dumps(results,indent=2))
