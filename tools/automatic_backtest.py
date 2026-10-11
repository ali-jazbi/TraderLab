"""Diagnostic replay of normalized genuine market inputs; no trades or PnL."""
import argparse
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from traderlab.replay import Engine, digest, json_line


def diagnose(events: Path, config: Path, output: Path):
    if output.exists():
        raise ValueError('Output already exists; choose a fresh directory')
    engine = Engine(json.loads(config.read_text(encoding='utf-8'), parse_float=Decimal))
    inputs, frames = Counter(), Counter()
    first = last = None
    with events.open(encoding='utf-8') as stream:
        for index, line in enumerate(stream, 1):
            try:
                row = json.loads(line, parse_float=Decimal)
                if row['kind'] not in ('bar', 'tick'):
                    raise ValueError('Diagnostic backtest accepts market bars/ticks only; annotations are forbidden')
                engine.accept(row)
            except (ValueError, KeyError, TypeError) as error:
                raise ValueError(f'Input line {index}: {error}') from error
            inputs[row['kind']] += 1
            if row['kind'] == 'bar':
                frames[row['timeframe']] += 1
            first = first or row['time']
            last = row['time']
    if engine.positions or engine.setups:
        raise ValueError('Diagnostic-only invariant failed')
    counts = Counter(e['event'] for e in engine.events)
    by_frame = Counter((e['event'], e['timeframe']) for e in engine.events if 'timeframe' in e)
    blocked = [e for e in engine.events if e['event'] == 'AUTO_SETUP_BLOCKED']
    reasons = Counter(r for e in blocked for r in e['reasons'])
    summary = {
        'mode': 'automatic_diagnostic_only', 'performance_available': False,
        'source_broker_symbol': engine.broker_symbol, 'strategy_symbol': 'XAUUSD',
        'input_sha256': digest(events), 'config_sha256': digest(config),
        'spec_sha256': digest(Path(__file__).resolve().parents[1] / 'docs/sources/canonical-strategy.fa.md'),
        'code_sha256': {p.name: digest(p) for p in sorted((Path(__file__).resolve().parents[1] / 'traderlab').glob('*.py'))},
        'first_observed_utc': first, 'last_observed_utc': last,
        'inputs': dict(inputs), 'bars_by_timeframe': dict(frames),
        'event_counts': dict(sorted(counts.items())),
        'counts_by_timeframe': {f'{event}/{tf}': n for (event, tf), n in sorted(by_frame.items())},
        'fully_confirmed_automatic_setups': counts['AUTO_SETUP_CONFIRMED'],
        'blocked_automatic_relationships': len(blocked), 'blocked_reasons': dict(sorted(reasons.items())),
        'fvg_validity_at_end': dict(Counter(g['fill_state'] for g in engine.automatic.gaps.values())),
        'relationship_samples': blocked[:20],
        'bos_samples': [e for e in engine.events if e['event'] == 'BOS_CONFIRMED'][:20],
        'limits': ['Same-timeframe geometric containment only; no approved cross-timeframe association or BOS grouping',
                   'FVG_CONFIRMED counts geometry; FULL is invalid and PARTIAL policy remains unresolved',
                   'Initial warm-up bars become available at capture time, never retrospectively',
                   'No paper trades, win rate or profitability are inferred'],
    }
    output.mkdir(parents=True)
    (output / 'events.jsonl').write_text(''.join(json_line(e) for e in engine.events), encoding='utf-8')
    summary['journal_sha256'] = digest(output / 'events.jsonl')
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--events', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        report = diagnose(args.events, args.config, args.out)
    except (ValueError, OSError) as error:
        parser.exit(2, f'Diagnostic replay failed: {error}\n')
    print(json.dumps({k: report[k] for k in ('inputs', 'event_counts', 'fully_confirmed_automatic_setups',
                                           'blocked_automatic_relationships', 'journal_sha256')}, indent=2))


if __name__ == '__main__':
    main()
