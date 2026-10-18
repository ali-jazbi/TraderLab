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

def server_window(start, end):
    if start is None and end is None:return None
    if not start or not end:raise ValueError('Both server window endpoints are required')
    a,b=datetime.fromisoformat(start),datetime.fromisoformat(end)
    if a.tzinfo is not None or b.tzinfo is not None or b<=a:
        raise ValueError('Increasing broker server times without a timezone are required')
    return a.isoformat(timespec='milliseconds'),b.isoformat(timespec='milliseconds')

def validate_deal_window(positions, window):
    if window is None:return
    for rows in positions.values():
        for d in rows:
            # OnTester logs all deals at test end. The deal's own broker epoch,
            # never the log event's timestamp, determines the measured window.
            actual=datetime.fromtimestamp(d['deal_time_msc']/1000,timezone.utc).replace(tzinfo=None).isoformat(timespec='milliseconds')
            if not window[0]<=actual<window[1]:
                raise ValueError('Actual deal outside measured window; warm-up traded or an exit was censored')

def audit(folder, server_from=None, server_until=None):
    window=server_window(server_from,server_until)
    report=next(folder.glob('*.html')); blob=report.read_bytes(); cells=Cells()
    cells.feed(blob.decode('utf-16' if blob[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig'))
    labels=['History Quality:','Bars:','Ticks:','Total Trades:','Total Deals:','Total Net Profit:',
            'Gross Profit:','Gross Loss:','Profit Factor:','Equity Drawdown Maximal:',
            'Profit Trades (% of total):','Loss Trades (% of total):']
    metrics={k:cells.cells[cells.cells.index(k)+1] for k in labels if k in cells.cells}
    if metrics.get('History Quality:')!='100% real ticks':raise ValueError('Real-tick quality missing')
    raw=next((folder/'native-files').glob('POL*.jsonl')); digest=hashlib.sha256()
    events=[];groups=Counter();returns=Counter();dispatch=Counter();ticks=0;measured_ticks=0;warmup_ticks=0;last_tick=None;frozen={}
    for line in raw.open('rb'):
        digest.update(line)
        if b'"event":"TICK"' in line:
            ticks+=1;last_tick=line
            if window is not None:
                at=line.split(b'"server_time":"',1)[1][:23].decode('ascii')
                measured_ticks+=window[0]<=at<window[1]
                warmup_ticks+=at<window[0]
            continue
        if not any(s in line for s in (b'TESTER_CORE_',b'CORE_CONTROLLER_SUMMARY',b'TICK_CAPTURE_SUMMARY',
                b'EXPERIMENTAL_GROUP_FINALIZED',b'EXPERIMENTAL_FIRST_RETURN',b'CORE_TESTER_DISPATCH_RESULT')):continue
        r=json.loads(line);kind=r['event'];measured=window is None or window[0]<=r['server_time']<window[1]
        if kind=='EXPERIMENTAL_GROUP_FINALIZED':
            if measured:groups[r['reason'] or 'ACCEPTED']+=1
            frozen[r['fvg_id']]=r # Earlier context must survive; never reselect membership at the window start.
        elif kind=='EXPERIMENTAL_FIRST_RETURN':
            if measured:returns[r['reason']]+=1
        else:
            events.append(r)
            if kind=='CORE_TESTER_DISPATCH_RESULT':
                if not measured and r['submitted']:raise ValueError('Submitted setup outside measured window')
                if measured:dispatch[r['reason'] or 'SUBMITTED']+=1
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
    validate_deal_window(positions,window)
    entries=sum(d['entry_kind']==0 for rows in positions.values() for d in rows)
    closed=sum(any(d['entry_kind']==1 for d in rows) for rows in positions.values())
    if closed!=native['trades'] or closed!=int(metrics['Total Trades:']):raise ValueError('Closed positions do not reconcile')
    actual_net=sum((Decimal(str(d['net'])) for rows in positions.values() for d in rows),Decimal(0))
    if abs(actual_net-Decimal(metrics['Total Net Profit:'].replace(' ','')))>Decimal('.005'):raise ValueError('Deal costs/PnL do not reconcile')
    preset=next(folder.glob('*.set')).read_text(encoding='utf-16')
    inputs=dict(line.split('=',1) for line in preset.splitlines() if '=' in line)
    return {'run':folder.parent.name+'/'+folder.name,'archive':str(folder),'raw_sha256':digest.hexdigest(),
        **({'measured_server_window':window,'measured_ticks':measured_ticks,'warmup_ticks':warmup_ticks,
            'post_window_ticks':ticks-measured_ticks-warmup_ticks,
            'all_actual_deals_inside_window':True} if window is not None else {}),
        'compiled_binary_sha256':hashlib.sha256((folder/'tested.ex5').read_bytes()).hexdigest(),
        'raw_bytes':raw.stat().st_size,'native_report_sha256':hashlib.sha256(blob).hexdigest(),
        'native_report_metrics':metrics,'ticks':ticks,'group_reasons':dict(groups),'first_return_reasons':dict(returns),
        'dispatch_results':dict(dispatch),'inputs':inputs,'actual_entry_deals':entries,'actual_closed_positions':closed,
        'deal_net_reconciled':str(actual_net),'events':events,'positions':positions}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folders',nargs='+',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--server-from');p.add_argument('--server-until')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);results=[]
    for folder in a.folders:
        r=audit(folder,a.server_from,a.server_until);results.append(r);target=a.out/(folder.parent.name+'-'+folder.name);target.mkdir()
        for f in folder.iterdir():
            if f.suffix.lower() in ('.html','.png','.set','.ini'):shutil.copy2(f,target/f.name)
        print(r['run'],r['native_report_metrics'],r['dispatch_results'])
    (a.out/'results.json').write_text(json.dumps(results,indent=2))
