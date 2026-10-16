"""Read a native capture once. No market downloads, orders, replay or altered ticks.

Reports selected extremes and the first return's before/after fill state. Missing
evidence is unavailable, never a zero-trade result. Does not certify Demo readiness.
"""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path


def ids(value):
    return value.split(';') if isinstance(value, str) and value else value or []


def audit(capture):
    path = Path(capture)
    if not path.is_file():
        return {'status': 'BLOCKED_MISSING_RAW_CAPTURE', 'capture': str(path),
                'simulated_entry_orders': None, 'closed_trades': None,
                'net_profit': None, 'win_rate': None, 'profit_factor': None,
                'max_equity_drawdown': None, 'automatic_demo_ready': False}
    digest = hashlib.sha256()
    reasons = Counter()
    relations, groups, fill, changes = {}, {}, {}, {}
    summary = controller = configuration = metrics = None
    tick_count = previous_seq = 0
    entry_orders = set()
    invalid = []
    with path.open('rb') as stream:
        for line in stream:
            digest.update(line)
            if not line.strip():
                continue
            row = json.loads(line)
            if row['seq'] <= previous_seq:
                raise ValueError('Non-increasing capture sequence')
            previous_seq = row['seq']
            event = row['event']
            if event in ('TICK_CAPTURE_ERROR', 'TICK_CAPTURE_AMBIGUITY',
                         'CORE_CONTROLLER_HALTED', 'BOS_TRACKER_HALTED'):
                invalid.append({'event': event, 'seq': row['seq']})
            if event == 'TICK':
                tick_count += 1
                if row['tick_index'] != tick_count:
                    raise ValueError('Missing or reordered ticks')
            elif event == 'CORE_SETUP_CANDIDATE':
                key = (row['fvg_id'], row['bos_id'])
                # Geometry at first as-of observation; never substitute a later return.
                relations.setdefault(key, {k: row[k] for k in
                    ('side', 'bos_level', 'entry_reference', 'fvg', 'fill_state')})
                fill.setdefault(row['fvg_id'], row['fill_state'])
            elif event == 'CORE_FVG_VALIDITY_CHANGED':
                key = row['fvg_id']
                changes[key] = {'tick_index': row['tick_index'],
                    'before': row.get('fill_before_tick', fill.get(key, 'UNKNOWN')),
                    'after': row['fill_state']}
                fill[key] = row['fill_state']
            elif event == 'EXPERIMENTAL_GROUP_FINALIZED':
                reasons[row.get('reason') or 'ACCEPTED'] += 1
                if not row['accepted']:
                    continue
                members = ids(row['members'])
                selected = ids(row.get('selected_bos_ids'))
                known = [(b, relations[(row['fvg_id'], b)]) for b in members
                         if (row['fvg_id'], b) in relations]
                if not selected and known:
                    ordered = sorted(known, key=lambda v: (Decimal(v[1]['bos_level']), v[0]))
                    selected = [ordered[0][0], ordered[-1][0]]
                groups[row['fvg_id']] = {'finalized': row, 'selected_bos_ids': selected,
                    'selected_geometry': {b: r for b, r in known if b in selected},
                    'first_returns': {}, 'last_dispatch': None}
            elif event == 'EXPERIMENTAL_FIRST_RETURN':
                for key, group in groups.items():
                    if row['bos_id'] not in group['selected_bos_ids']:
                        continue
                    state = changes.get(key, {})
                    same_tick = state.get('tick_index') == row['tick_index']
                    group['first_returns'].setdefault(row['bos_id'], {'event': row,
                        'fill_before_tick': state.get('before') if same_tick else fill.get(key, 'UNKNOWN'),
                        'fill_after_tick': fill.get(key, 'UNKNOWN'),
                        'changed_on_return_tick': same_tick})
            elif event == 'CORE_TESTER_DISPATCH_RESULT':
                key = row['setup_id'].removeprefix('EXPERIMENTAL:')
                if key in groups:
                    groups[key]['last_dispatch'] = row
            elif event == 'TESTER_CORE_DEAL' and row['entry_kind'] == 0:
                entry_orders.add(row['deal'])
            elif event == 'TESTER_CORE_METRICS':
                metrics = row
            elif event == 'EXPERIMENTAL_TESTER_CONFIG':
                configuration = row
            elif event == 'TICK_CAPTURE_SUMMARY':
                summary = row
            elif event == 'CORE_CONTROLLER_SUMMARY':
                controller = row
    complete = bool(tick_count > 0 and summary and controller and metrics and
        summary.get('terminal_cursor_evidence_valid') is True and
        summary.get('capture_halted') is False and controller.get('controller_halted') is False and
        summary['emitted_ticks'] == tick_count == controller['processed_ticks'])
    configured = bool(configuration and configuration.get('simulated_transport_only') is True and
        configuration.get('real_and_demo_auto_submission') is False and
        all(v in configuration.get('status', '') for v in ('JOURNAL OK', 'PAIR LIMITS OK', 'CALENDAR_OK')))
    valid = complete and configured and not invalid and len(entry_orders) >= metrics.get('trades', 0)
    closed = metrics.get('trades') if valid else None
    for group in groups.values():
        group['final_condition'] = ('NO_SELECTED_POST_AVAILABILITY_FIRST_RETURN_IN_CAPTURE'
            if not group['first_returns'] else 'SEE_FIRST_RETURN_AND_DISPATCH_EVIDENCE')
        group['interior_entry_requires_unresolved_partial_permission'] = {
            b: Decimal(r['fvg'][0]) < Decimal(r['entry_reference']) < Decimal(r['fvg'][1])
            for b, r in group['selected_geometry'].items()}
    result = {'status': 'CAPTURE_VALID_MODEL_AND_BROKER_COSTS_REQUIRE_TESTER_REPORT' if valid else 'BLOCKED_INCOMPLETE_OR_INVALID_CAPTURE',
        'capture': str(path), 'sha256': digest.hexdigest(), 'ticks': tick_count,
        'group_reasons': dict(reasons), 'accepted_groups': groups,
        'invalid_events': invalid, 'configuration': configuration,
        'simulated_entry_orders': len(entry_orders) if valid else None,
        'closed_trades': closed, 'automatic_demo_ready': False,
        'raw_native_metrics': metrics}
    for key in ('net_profit', 'win_rate', 'profit_factor', 'max_equity_drawdown'):
        result[key] = metrics.get(key) if valid and closed else None
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.capture)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(result['status'])
    raise SystemExit(0 if result['status'].startswith('CAPTURE_VALID') else 2)
