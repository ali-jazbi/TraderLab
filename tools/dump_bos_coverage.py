"""Read-only native BOS coverage audit, independent of trading-package selection."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from traderlab.detection import Bar, Detector

START = '2026-10-13T17:00:00+00:00'
END = '2026-10-13T18:10:00+00:00'
EXPECTED_SHA256 = 'b035f959a324f0cc818f1a757ffe988c484313f4492742ef75800b1cad1c7591'
RELATED_FVGS = ('M1:BUY:2026-10-13T18:05:00+00:00', 'M1:BUY:2026-10-13T18:06:00+00:00')


def instant(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def server(value):
    return (instant(value) + timedelta(hours=3)).replace(tzinfo=None).isoformat(timespec='milliseconds')


def extract(path):
    """Hash the original while retaining actual closed candles/events, never rewriting it."""
    start, end = instant(START), instant(END)
    ids = {f'M1:{side}:{(start + timedelta(minutes=n)).isoformat()}'
           for n in range(int((end-start).total_seconds()/60)) for side in ('BUY', 'SELL')}
    needles = tuple(x.encode() for x in sorted(ids))
    bars, events, groups = [], [], []
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for line in source:
            digest.update(line)
            if b'"event":"TICK"' in line:
                continue
            if b'"event":"BOS_TRACKER_CLOSED_BAR"' in line and b'"timeframe":"M1"' in line:
                row = json.loads(line)
                if instant(row['opened_at']) >= start:
                    bars.append(row)
            elif b'"event":"EXPERIMENTAL_GROUP_FINALIZED"' in line:
                row = json.loads(line)
                if row.get('fvg_id') in RELATED_FVGS:
                    groups.append(row)
            elif (b'"bos_id":"M1:' in line
                  and (b'M1:BUY:2026-10-13T17:' in line or b'M1:SELL:2026-10-13T17:' in line
                       or b'M1:BUY:2026-10-13T18:0' in line or b'M1:SELL:2026-10-13T18:0' in line)
                  and any(n in line for n in needles)):
                row = json.loads(line)
                if row.get('bos_id') in ids:
                    events.append(row)
    if digest.hexdigest() != EXPECTED_SHA256:
        raise ValueError('Raw capture hash does not match the independently verified source')
    return compact(dict(source=str(path), sha256=digest.hexdigest(), timeframe='M1',
                        candle_start_utc=START, candle_end_utc_exclusive=END,
                        server_utc_offset_seconds=10800, bars=bars, events=events, related_groups=groups))


def compact(evidence):
    """Keep the full seed-to-terminal candle sequence and only relevant native facts."""
    terminals = [e for e in evidence['events'] if e['event'] in ('CORE_BOS_CONFIRMED', 'CORE_BOS_REJECTED')]
    if len({e['bos_id'] for e in terminals}) == 140:
        last = max(instant(e['time']) for e in terminals)
        evidence['bars'] = [b for b in evidence['bars'] if instant(b['time']) <= last]
    names = {'CORE_BOS_CANDIDATE_QUALIFIED', 'CORE_BOS_CONFIRMED', 'CORE_BOS_REJECTED',
             'BOS_INTRABAR_BREAK', 'BOS_FIRST_DIRECTIONAL_RETURN', 'EXPERIMENTAL_FIRST_RETURN'}
    evidence['events'] = [e for e in evidence['events'] if e['event'] in names or
                          (e['event'] == 'CORE_SETUP_CANDIDATE' and e.get('fvg_id') in RELATED_FVGS)]
    return evidence


def coverage(evidence):
    """Replay every seed; join native diagnostics without filtering consumed BOSs."""
    start, end = instant(START), instant(END)
    detector, rows = Detector(), {}
    by_id = {}
    for e in evidence['events']:
        by_id.setdefault(e['bos_id'], []).append(e)
    for record in evidence['bars']:
        bar = Bar.read(record)
        for event in detector.accept(bar):
            if event['event'] not in ('BOS_CANDIDATE_QUALIFIED', 'BOS_CONFIRMED', 'BOS_REJECTED'):
                continue
            key = f"M1:{event['side']}:{event['candidate_at'].isoformat()}"
            if key not in rows:
                continue
            row = rows[key]
            if event['event'] == 'BOS_CANDIDATE_QUALIFIED':
                row.update(qualification_candle_server=server(record['opened_at']),
                           qualification_observed_server=record['server_time'],
                           qualification_close=record['close'],
                           qualification_reason='later_close_below_candidate_low' if event['side'] == 'BUY'
                           else 'later_close_above_candidate_high')
            else:
                row.update(status='ACCEPTED' if event['event'] == 'BOS_CONFIRMED' else 'REJECTED',
                           break_candle_server=server(record['opened_at']),
                           closed_break_observed_server=record['server_time'],
                           reject_reason='' if event['event'] == 'BOS_CONFIRMED' else event['reason'])
        if start <= bar.opened < end:
            for side in ('BUY', 'SELL'):
                key = f'M1:{side}:{bar.opened.isoformat()}'
                rows[key] = dict(bos_id=key, candle_server=server(record['opened_at']), candle_utc=record['opened_at'],
                                 side=side, wick_level=record['high' if side == 'BUY' else 'low'],
                                 high=record['high'], low=record['low'], qualification_candle_server='',
                                 qualification_observed_server='', qualification_close='', qualification_reason='',
                                 break_candle_server='', closed_break_observed_server='',
                                 intrabar_bid_break_server='', intrabar_ask_break_server='',
                                 status='PENDING_AT_CAPTURE_END', reject_reason='',
                                 native_status='', detector_merge_dedup_rule='NONE',
                                 first_bid_return_server='', package_relation_reasons='')
    for key, row in rows.items():
        native = by_id.get(key, [])
        terminal = [e for e in native if e['event'] in ('CORE_BOS_CONFIRMED', 'CORE_BOS_REJECTED')]
        row['native_status'] = ('ACCEPTED' if terminal[0]['event'] == 'CORE_BOS_CONFIRMED' else 'REJECTED') if terminal else 'PENDING_AT_CAPTURE_END'
        if len(terminal) > 1 or row['native_status'] != row['status']:
            raise ValueError(f'Native/Python status mismatch: {key}')
        if terminal and terminal[0]['reason'] != (row['reject_reason'] or 'qualified_before_break'):
            raise ValueError(f'Native/Python rejection mismatch: {key}')
        qualified = [e for e in native if e['event'] == 'CORE_BOS_CANDIDATE_QUALIFIED']
        if len(qualified) > 1 or (qualified[0]['server_time'] if qualified else '') != row['qualification_observed_server']:
            raise ValueError(f'Native/Python qualification mismatch: {key}')
        for event in native:
            if event['event'] == 'BOS_INTRABAR_BREAK':
                row[f"intrabar_{event['break_quote']}_break_server"] = event['server_time']
            elif event['event'] == 'BOS_FIRST_DIRECTIONAL_RETURN' and event['break_quote'] == event['retest_quote'] == 'bid':
                row['first_bid_return_server'] = event['server_time']
        reasons = {f"{e['fvg_id']}:{e.get('reasons', '')}" for e in native if e['event'] == 'CORE_SETUP_CANDIDATE'}
        row['package_relation_reasons'] = ' | '.join(sorted(reasons))
    return list(rows.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    evidence = extract(args.capture)
    rows = coverage(evidence)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    (out/'evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    with (out/'candidates.csv').open('w', newline='', encoding='utf-8-sig') as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    summary = dict(candidates=len(rows), statuses=dict(Counter(r['status'] for r in rows)),
                   native_python_disagreements=0, detector_deduplication='NONE', source_sha256=evidence['sha256'])
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary))
    for row in rows:
        if row['side'] == 'BUY' and row['candle_server'][11:16] in ('20:16', '20:24', '20:49'):
            print(json.dumps(row, ensure_ascii=False))


if __name__ == '__main__':
    main()
