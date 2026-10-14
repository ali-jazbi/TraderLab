"""Compare original Python detector against genuine as-of native closed candles.

This compares detections, not the tick-driven trade lifecycle or profitability.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from traderlab.detection import Bar, Detector
from traderlab.replay import encode


def compare(capture):
    detector=Detector(); counts=Counter(); summary=None; bars=0; fvgs=[]
    with Path(capture).open('rb') as stream:
        for raw in stream:
            if b'"event":"CORE_CONTROLLER_SUMMARY"' in raw:
                summary=json.loads(raw)
            if b'"event":"BOS_TRACKER_CLOSED_BAR"' not in raw:
                continue
            row=json.loads(raw); bar=Bar.read({**row,'kind':'bar','symbol':'XAUUSD_o'})
            for o in detector.accept(bar):
                counts[o['event']]+=1
                if o['event']=='FVG_CONFIRMED':
                    fvgs.append(encode(o))
            bars+=1
    if summary is None or summary['controller_halted']:
        raise ValueError('Completed nonhalted native summary required')
    return dict(scope='closed-candle detections only, NOT full trade lifecycle parity',
                closed_bars=bars,python_event_counts=dict(counts),native_fvgs=summary['fvgs'],
                native_qualified_bos=summary['qualified_bos'],
                fvg_count_match=counts['FVG_CONFIRMED']==summary['fvgs'],
                qualified_bos_count_match=counts['BOS_CANDIDATE_QUALIFIED']==summary['qualified_bos'],
                python_fvg_examples=fvgs[:3],full_lifecycle_parity=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',required=True)
    print(json.dumps(compare(p.parse_args().capture),indent=2))
