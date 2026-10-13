"""Chronological review of genuine Core observations. Never emits a setup or trade."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from traderlab.core_packages import first_return_issue
from traderlab.replay import digest

def review(path):
    counts=Counter(); candidates={}; observations=[]; summary=None; capture=None
    last_seq=0; last_tick=None
    with path.open(encoding='utf-8-sig') as f:
        for line in f:
            r=json.loads(line); seq=r['seq']
            if seq<=last_seq: raise ValueError('Capture sequencing regression')
            last_seq=seq; counts[r['event']]+=1
            if r['event']=='TICK':
                if last_tick is not None and (r['tick_index']!=last_tick['tick_index']+1 or r['time']<last_tick['time']):
                    raise ValueError('Market tick chronology/coverage regression')
                last_tick=r
            elif r['event'] in ('CORE_SETUP_CANDIDATE','CORE_FIRST_RETURN_BLOCKED'):
                if not last_tick or r['time']<last_tick['time']: raise ValueError('Core observation regressed')
                candidates[r['candidate_id']]=r
                if r['first_return_consumed']: observations.append(r)
            elif r['event']=='CORE_CONTROLLER_SUMMARY': summary=r
            elif r['event']=='TICK_CAPTURE_SUMMARY': capture=r
    if not summary or summary['controller_halted'] or summary['processed_ticks']!=counts['TICK']:
        raise ValueError('Complete nonhalted Core capture required')
    if not capture or capture.get('capture_halted') or not capture.get('terminal_cursor_evidence_valid'):
        raise ValueError('Complete loss-aware terminal-history evidence required')
    reasons=Counter(first_return_issue(r) or 'NECESSARY_ENTRY_EVIDENCE_ONLY_PACKAGE_UNAPPROVED' for r in observations)
    return {'capture_sha256':digest(path),'ticks':counts['TICK'],'candidate_pairs':len(candidates),
            'first_return_observations':len(observations),'first_return_reasons':dict(reasons),
            'unfilled_exact_returns_after_confirmation':sum(first_return_issue(r) is None for r in observations),
            'automatic_core_ready':False,'approved_automatic_setups':0,'operator_packages_supplied':0,
            'simulated_or_broker_trades':0,'pnl':None,
            'minimum_missing_decision':'Exact package membership and finalization: FVG/OB IDs plus complete BOS member IDs',
            'controller_summary':summary}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('--out',type=Path)
    a=p.parse_args();r=review(a.capture)
    if a.out:a.out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r,indent=2))
