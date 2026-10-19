"""BOS age audit and fixed retrospective cohorts of actual native Tester deals.

No synthetic fills, no new backtest or production expiry. Thresholds are study
assumptions measured from candidate candle opening, not qualification or break.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
from decimal import Decimal as D
import gzip
import hashlib
import json
from pathlib import Path

from tools.report_discovery_study import performance

CAPTURE_SHA = 'b035f959a324f0cc818f1a757ffe988c484313f4492742ef75800b1cad1c7591'
ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT/'docs/reports/auto-core-discovery-20261018'


def at(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def age_ms(candidate, observed):
    delta = at(observed)-at(candidate)
    return (delta.days*86400+delta.seconds)*1000+delta.microseconds//1000


def age_allowed(timeframe, candidate, observed, cap):
    """Offline TESTER-study predicate. Inclusive fixed 60/120 minute boundaries."""
    if cap not in (0, 60, 120):
        raise ValueError('Only unchanged0 and prespecified study60/120 are authorized')
    if cap == 0 or timeframe != 'M1':
        return True
    return 0 <= age_ms(candidate, observed) <= cap*60000


def minutes(candidate, observed):
    return str(D(age_ms(candidate, observed))/60000) if observed else ''


def server(value, offset=10800):
    return (at(value)+timedelta(seconds=offset)).replace(tzinfo=None).isoformat(timespec='milliseconds') if value else ''


def scan(path):
    bos, relations, returns = {}, {}, []
    digest = hashlib.sha256()
    wanted = (b'"event":"CORE_BOS_', b'"event":"BOS_INTRABAR_BREAK"',
              b'"event":"BOS_FIRST_DIRECTIONAL_RETURN"', b'"event":"CORE_SETUP_CANDIDATE"',
              b'"event":"EXPERIMENTAL_FIRST_RETURN"')
    first_tick = last_tick = None
    with Path(path).open('rb') as source:
        for line in source:
            digest.update(line)
            if b'"event":"TICK"' in line:
                stamp = line.split(b'"server_time":"', 1)[1][:23].decode()
                first_tick = first_tick or stamp; last_tick = stamp
                continue
            if not any(token in line for token in wanted):
                continue
            e = json.loads(line)
            if e['server_utc_offset_seconds'] != 10800:
                raise ValueError('This source-specific audit requires its recorded UTC+3 offset')
            key = e.get('bos_id')
            if not key:
                continue
            if e['event'] == 'CORE_BOS_CANDIDATE_QUALIFIED':
                tf, side, candle = key.split(':', 2)
                if key in bos:
                    raise ValueError('Duplicate native qualification: '+key)
                bos[key] = dict(bos_id=key, timeframe=tf, side=side, candidate_at=candle,
                                wick_level=e['level'], qualified_at=e['time'], bid_break_at='',
                                ask_break_at='', first_bid_touch_at='', first_ask_touch_at='',
                                structural_status='QUALIFIED_PENDING_BREAK')
            elif key in bos:
                b = bos[key]
                if e['event'] == 'CORE_BOS_CONFIRMED':
                    b['structural_status'] = 'CONFIRMED'
                elif e['event'] == 'BOS_INTRABAR_BREAK':
                    b[e['break_quote']+'_break_at'] = e['time']
                elif e['event'] == 'BOS_FIRST_DIRECTIONAL_RETURN' and e['break_quote'] == 'bid':
                    b['first_'+e['retest_quote']+'_touch_at'] = e['time']
                elif e['event'] == 'CORE_SETUP_CANDIDATE':
                    relations[(key, e['fvg_id'])] = {k:e[k] for k in
                        ('bos_id', 'fvg_id', 'formation_at', 'fvg_available_at', 'fill_state', 'reasons')}
                elif e['event'] == 'EXPERIMENTAL_FIRST_RETURN':
                    returns.append(dict(bos_id=key, time=e['time'], server_time=e['server_time'],
                                        signal_ready=e['signal_ready'], reason=e['reason'],
                                        age_minutes=minutes(b['candidate_at'], e['time'])))
    if digest.hexdigest() != CAPTURE_SHA:
        raise ValueError('Original source hash mismatch')
    return dict(source=str(path), source_sha256=digest.hexdigest(), first_tick_server=first_tick,
                last_tick_server=last_tick, bos=list(bos.values()), relations=list(relations.values()), returns=returns)


def entries(evidence):
    index = {b['bos_id']: b for b in evidence['bos']}
    records = []
    for label in ('final-training', 'final-holdout'):
        result_path = STUDY/label/'results.json'
        result = json.loads(result_path.read_text())[0]
        p = json.loads((STUDY/label/'performance.json').read_text())[0]
        dispatch = [e for e in result['events'] if e['event'] == 'CORE_TESTER_DISPATCH_RESULT' and e['submitted']]
        for position in p['actual_positions']:
            matches = [e for e in dispatch if e['setup_id'] == position['setup'] and
                       datetime.fromisoformat(e['server_time']) == datetime.fromisoformat(position['entry_time'])]
            if len(matches) != 1:
                raise ValueError('Missing unique native dispatch for actual deal')
            e = matches[0]; group = e['frozen_group']
            selected = [index[key] for key in group['selected_bos_ids'].split(';')
                        if D(index[key]['wick_level']) + (D('.5') if index[key]['side'] == 'BUY' else D('-.5')) == D(position['planned'])]
            if len(selected) != 1:
                raise ValueError('Ambiguous selected BOS identity; no hindsight assignment')
            b = selected[0]
            record = dict(window=label, run=p['run'], setup=position['setup'], bos_id=b['bos_id'],
                          position=position['position'], leg=position['leg'], timeframe=b['timeframe'], side=b['side'],
                          wick_level=b['wick_level'], candle_server=server(b['candidate_at']),
                          qualification_server=server(b['qualified_at']), break_server=server(b['bid_break_at']),
                          fvg_id=group['fvg_id'], fvg_confirmation_server=group['server_time'],
                          first_touch_server=server(b['first_bid_touch_at']),
                          actual_entry_server=datetime.fromisoformat(position['entry_time']).isoformat(timespec='milliseconds'),
                          age_at_touch_minutes=minutes(b['candidate_at'], b['first_bid_touch_at']),
                          age_at_entry_minutes=minutes(b['candidate_at'], e['time']),
                          actual_entry_price=position['entry'], actual_exit_server=position['exit_time'],
                          actual_exit_price=position['exit'], net=position['net'])
            for cap in (60, 120):
                record[f'allowed_{cap}'] = age_allowed(b['timeframe'], b['candidate_at'], e['time'], cap)
            records.append(record)
    return records


def cohorts(records):
    output = []
    for window in sorted({r['window'] for r in records}):
        original = [r for r in records if r['window'] == window]
        for cap in (0, 60, 120):
            kept = [r for r in original if cap == 0 or r[f'allowed_{cap}']]
            removed = [r for r in original if r not in kept]
            setups = defaultdict(lambda:D(0))
            for r in kept:
                setups[r['setup']] += D(r['net'])
            output.append(dict(window=window, experiment='UNCHANGED' if cap == 0 else f'EXPERIMENTAL_M1_AGE_{cap}',
                               retained_positions=performance(D(r['net']) for r in kept),
                               removed_positions=performance(D(r['net']) for r in removed),
                               retained_setup_cohort=performance(setups.values()),
                               removed_entry_pairs=len({(r['bos_id'], r['actual_entry_server']) for r in removed}),
                               retained_entry_pairs=len({(r['bos_id'], r['actual_entry_server']) for r in kept}),
                               type='RETROSPECTIVE_ACTUAL_DEAL_COHORT_NOT_RERUN',
                               causal_backtest_performance=None, equity_drawdown=None))
    return output


def write_csv(path, rows):
    if not rows:
        return
    opener = gzip.open if path.suffix == '.gz' else Path.open
    mode = 'wt' if path.suffix == '.gz' else 'w'
    with opener(path, mode, encoding='utf-8-sig', newline='') as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def write_report(evidence, out):
    records = entries(evidence)
    out.mkdir(parents=True, exist_ok=False)
    write_csv(out/'actual-entry-ages.csv', records)
    linked = defaultdict(list)
    for r in evidence['relations']:
        linked[r['bos_id']].append(r)
    all_bos = []
    for b in evidence['bos']:
        row = dict(bos_id=b['bos_id'], timeframe=b['timeframe'], side=b['side'], wick_level=b['wick_level'],
                   candle_server=server(b['candidate_at']), qualification_server=server(b['qualified_at']),
                   bid_break_server=server(b['bid_break_at']), ask_break_server=server(b['ask_break_at']),
                   first_bid_touch_server=server(b['first_bid_touch_at']), first_ask_touch_server=server(b['first_ask_touch_at']),
                   age_at_bid_touch_minutes=minutes(b['candidate_at'], b['first_bid_touch_at']),
                   structural_status=b['structural_status'],
                   fvg_confirmations=';'.join(r['fvg_id']+'@'+server(r['fvg_available_at']) for r in linked[b['bos_id']]),
                   actual_entries=';'.join(r['window']+':'+r['position']+'@'+r['actual_entry_server'] for r in records if r['bos_id'] == b['bos_id']))
        all_bos.append(row)
    write_csv(out/'all-qualified-bos.csv.gz', all_bos)
    write_csv(out/'fvg-relations.csv.gz', evidence['relations'])
    signal_comparisons = []
    for name, start, end in (('training', '2026-10-07', '2026-10-10'), ('previously_inspected_holdout', '2026-10-14', '2026-10-17')):
        # The later native run consumes Oct7–9 during warm-up. These18 returns
        # match the earlier measured run's18 signal-ready events; no orders inferred.
        expected_reason = 'TESTER_WARMUP_RETURN_CONSUMED_NO_ORDER' if name == 'training' else 'AWAIT_CURRENT_TESTER_QUOTE_AND_STRATEGY_GUARDS'
        eligible = [r for r in evidence['returns'] if start <= r['server_time'][:10] < end and r['reason'] == expected_reason]
        lookup = {b['bos_id']: b for b in evidence['bos']}
        if len(eligible) != 18:
            raise ValueError('Signal-ready count differs from the original native report')
        for cap in (60, 120):
            rejected = [r for r in eligible if not age_allowed(lookup[r['bos_id']]['timeframe'], lookup[r['bos_id']]['candidate_at'], r['time'], cap)]
            signal_comparisons.append(dict(window=name, cap_minutes=cap, original_pre_execution_signals=len(eligible),
                                           age_blocked=len(rejected), age_blocked_signals=rejected,
                                           causal_replacements_unknown=True))
    selected = {r['bos_id'] for r in records} | {'M1:BUY:2026-10-13T17:16:00+00:00'}
    # Also retain the peer extreme needed to resolve each frozen plan's identity.
    for label in ('final-training', 'final-holdout'):
        for e in json.loads((STUDY/label/'results.json').read_text())[0]['events']:
            if e['event'] == 'CORE_TESTER_DISPATCH_RESULT' and e['submitted']:
                selected.update(e['frozen_group']['selected_bos_ids'].split(';'))
    fvgs = {r['fvg_id'] for r in records} | {'M1:BUY:2026-10-13T18:06:00+00:00'}
    fixture = dict(source=evidence['source'], source_sha256=evidence['source_sha256'],
                   scope='Selected genuine entries plus the owner20:16 example; complete BOS/relations tables are separate compressed CSVs',
                   bos=[b for b in evidence['bos'] if b['bos_id'] in selected],
                   relations=[r for r in evidence['relations'] if r['bos_id'] in selected and r['fvg_id'] in fvgs])
    (out/'evidence.json').write_text(json.dumps(fixture, indent=2)+'\n', encoding='utf-8')
    summary = dict(source_sha256=evidence['source_sha256'],
                   source_first_tick_server=evidence['first_tick_server'], source_last_tick_server=evidence['last_tick_server'],
                   qualified_by_timeframe=dict(Counter(b['timeframe'] for b in evidence['bos'])),
                   fvg_relation_count=len(evidence['relations']), signal_comparisons=signal_comparisons,
                   cohort_comparisons=cohorts(records), automatic_demo='LOCKED',
                   production_numerical_expiry_implemented=False,
                   unseen_validation='NOT_AVAILABLE: Oct7–9 and Oct14–16 were already inspected; no untouched outcome period is certified',
                   limitations=['Not a causal rerun; removing entries can change daily stops and subsequent trades.',
                                'No new native orders, performance or drawdown is claimed.',
                                'Age is from BOS candle opening; exact production cutoff remains unconfirmed.'])
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    write_report(scan(args.capture), args.out)


if __name__ == '__main__':
    main()
