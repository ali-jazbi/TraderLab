"""Read-only comparison against terminal history; preserves same-ms multiplicity.

This terminal's API exposes broker-clock time_msc, independently checked against
native capture. The explicit offset is not inferred from the operating system.
Never submits orders or modifies a capture.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path


def record(ms, bid, ask, last, volume):
    return f"{int(ms)}|{float(bid):.8f}|{float(ask):.8f}|{float(last):.8f}|{int(volume)}\n".encode()


def verify(capture, start, end):
    import MetaTrader5 as mt5
    if not mt5.initialize():
        raise RuntimeError(str(mt5.last_error()))
    api_hash = hashlib.sha256(); api_count = 0; baseline = None
    try:
        day = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
        stop = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
        while day < stop:
            # Query inclusive API interval without overlapping its next-day boundary.
            rows = mt5.copy_ticks_range("XAUUSD_o", day, day+timedelta(days=1,milliseconds=-1), mt5.COPY_TICKS_ALL)
            if rows is None:
                raise RuntimeError(str(mt5.last_error()))
            for r in rows:
                if baseline is None:
                    baseline = int(r['time_msc'])
                    continue  # accepted startup snapshot excludes this occurrence
                api_hash.update(record(r['time_msc'],r['bid'],r['ask'],r['last'],r['volume']))
                api_count += 1
            day += timedelta(days=1)
    finally:
        mt5.shutdown()
    native_hash = hashlib.sha256(); native_count = 0
    with Path(capture).open('rb') as stream:
        for line in stream:
            if b'"event":"TICK"' not in line:
                continue
            r=json.loads(line)
            native_hash.update(record(r['time_msc'],r['bid'],r['ask'],r['last'],r['volume']))
            native_count += 1
    result = dict(api_ticks_after_baseline=api_count,native_ticks=native_count,
                  api_sha256=api_hash.hexdigest(),native_sha256=native_hash.hexdigest(),
                  same_ordered_history=api_count==native_count and api_hash.digest()==native_hash.digest(),
                  startup_baseline_msc=baseline,quote_fields='time_msc,bid,ask,last,volume',
                  api_clock='explicit broker-clock epoch for this terminal; offset 10800',
                  flags_not_compared='tester strips API REAL flag; quote order and multiplicity are compared')
    if not result['same_ordered_history']:
        result['validity']='MISMATCH_REQUIRES_INVESTIGATION'
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',required=True);p.add_argument('--start',required=True);p.add_argument('--end',required=True)
    a=p.parse_args(); result=verify(a.capture,a.start,a.end)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['same_ordered_history'] else 1)
