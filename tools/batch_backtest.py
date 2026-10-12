"""Independent chronological paper cases; default market-only, no broker orders."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from traderlab.backtest import batch
from traderlab.replay import encode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--events', nargs='+', required=True, type=Path)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--allow-annotations', action='store_true', help='Explicit sourced simulation; never automatic historical approval')
    args = parser.parse_args()
    try:
        report = batch(args.events, args.config, args.out, args.allow_annotations)
    except (ValueError, OSError) as error:
        parser.exit(2, f'Batch rejected: {error}\n')
    print(json.dumps(encode({k: report[k] for k in ('accepted_cases', 'rejected_cases', 'simulated_trades',
        'historical_automatic_trades', 'fully_closed_trades', 'performance_available', 'win_rate',
        'realized_pnl_usd', 'automatic_demo_ready')}), indent=2))
    return 1 if report['rejected_cases'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
