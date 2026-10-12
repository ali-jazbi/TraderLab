"""Read-only native/Python diagnostic comparison; requires a fresh MT5 capture."""
import argparse
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.inspect_capture import inspect_capture
from traderlab.detection import instant
from traderlab.replay import Engine, digest

ROOT = Path(__file__).resolve().parents[1]
AUDITED = frozenset({'M1:BUY:2026-10-07T03:10:00+00:00',
                     'M5:SELL:2026-10-07T02:05:00+00:00'})
EVENTS = ('BOS_INTRABAR_BREAK', 'BOS_FIRST_DIRECTIONAL_RETURN')


def signature(row):
    key = (row['event'], row['bos_id'], row['break_quote'], row.get('retest_quote'))
    fields = ('break_at', 'qualified_at', 'level', 'observed_quote', 'tick_index') if row['event'] == EVENTS[0] else (
        'first_return_at', 'outbound_at', 'entry_reference', 'previous_quote', 'observed_quote',
        'exact_quote', 'consumed', 'tick_index')
    value = []
    for field in fields:
        item = row[field]
        if field.endswith('_at'):
            item = instant(item)
        elif field in ('level', 'observed_quote', 'previous_quote', 'entry_reference'):
            item = Decimal(str(item))
        value.append(item)
    return key, tuple(value)


def compare_rows(rows, config):
    """Core comparator, also exercised by explicitly non-native test fixtures."""
    summaries = [r for r in rows if r.get('event') == 'BOS_TRACKER_SUMMARY']
    ticks = [r for r in rows if r.get('event') == 'TICK']
    bars = [r for r in rows if r.get('event') == 'BOS_TRACKER_CLOSED_BAR']
    if len(summaries) != 1 or not bars or not ticks:
        raise ValueError('Fresh native tracker capture required; legacy logs cannot verify parity')
    summary = summaries[0]
    if summary.get('detection_halted') is not False or any(r.get('event') == 'BOS_TRACKER_HALTED' for r in rows):
        raise ValueError('Native detection halted; capture cannot verify detector parity')
    if summary.get('processed_ticks') != len(ticks) or summary.get('automatic_setups') != 0:
        raise ValueError('Native tick coverage/setup counters do not reconcile')
    counts = Counter(r.get('event') for r in rows)
    if summary.get('intrabar_breaks') != counts[EVENTS[0]] or summary.get('first_returns') != counts[EVENTS[1]]:
        raise ValueError('Native diagnostic event counters do not reconcile')
    # Unknown executable policies remain unknown. Both break lanes are diagnostic.
    config = {**config, 'observation_price_side': None}
    engine = Engine(config)
    pending_index = None
    pending_time = None
    last_tick = None
    for row in rows:
        if row.get('event') == 'BOS_TRACKER_CLOSED_BAR':
            if pending_index is not None and pending_index != row['before_tick_index']:
                raise ValueError('As-of bars span different tick dispatches')
            pending_index = row['before_tick_index']
            if pending_time is not None and pending_time != instant(row['time']):
                raise ValueError('As-of bars span different dispatch timestamps')
            pending_time = instant(row['time'])
            engine.accept({**row, 'kind': 'bar'})
        elif row.get('event') == 'TICK':
            if pending_index is not None and pending_index != row['tick_index']:
                raise ValueError('As-of bar does not immediately precede its dispatch tick')
            if pending_time is not None and pending_time != instant(row['time']):
                raise ValueError('As-of bar availability differs from dispatch tick timestamp')
            engine.accept({**row, 'kind': 'tick'})
            last_tick = row
            pending_index = None
            pending_time = None
        elif row.get('event') in EVENTS:
            quote = row['break_quote'] if row['event'] == EVENTS[0] else row['retest_quote']
            if last_tick is None or row['tick_index'] != last_tick['tick_index'] or \
                    instant(row['time']) != instant(last_tick['time']) or \
                    row['millisecond_ordinal'] != last_tick['millisecond_ordinal'] or \
                    Decimal(str(row['observed_quote'])) != Decimal(str(last_tick[quote])):
                raise ValueError('Native diagnostic is not linked to its genuine dispatch tick')
    if pending_index is not None or engine.setups or engine.positions:
        raise ValueError('Incomplete as-of stream or diagnostic-only invariant failed')
    observed, expected = {}, {}
    for records, target in ((rows, observed), (engine.events, expected)):
        for row in records:
            if row.get('event') not in EVENTS or row.get('bos_id') not in AUDITED:
                continue
            key, value = signature(row)
            if key in target:
                raise ValueError('Duplicate native/Python BOS lane diagnostic')
            target[key] = value
    missing_candidates = [key for key in sorted(AUDITED) if not any(k[1] == key for k in expected)]
    if missing_candidates:
        raise ValueError('Audited candidates absent from genuine input: ' + ', '.join(missing_candidates))
    differences = [':'.join(str(x) for x in key) for key in sorted(set(observed) | set(expected), key=str)
                   if observed.get(key) != expected.get(key)]
    return {'comparison_scope': 'two audited BOS candidates, both diagnostic break/return lanes',
            'matches': not differences, 'native_events': len(observed), 'python_events': len(expected),
            'differences': differences, 'ticks': len(ticks), 'tracker_bars': len(bars),
            'native_runtime': {k: summary.get(k) for k in ('processing_us', 'candidate_inspections',
                                                          'active_bos', 'stored_bos', 'copyrates_calls')},
            'full_native_python_parity': 'NOT_ESTABLISHED', 'automatic_setups': 0}


def compare_capture(path):
    inspected = inspect_capture(path)
    if inspected['errors']:
        raise ValueError('Raw capture integrity failed: ' + '; '.join(inspected['errors'][:5]))
    if inspected.get('tick_capture_summary') is None:
        raise ValueError('Loss-aware terminal history evidence required')
    config = json.loads((ROOT / 'configs/production.template.json').read_text(encoding='utf-8'))
    report = compare_rows(inspected['rows'], config)
    report['capture_sha256'] = digest(path)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    args = parser.parse_args()
    try:
        report = compare_capture(args.capture)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f'Comparison rejected: {error}\n')
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report['matches'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
