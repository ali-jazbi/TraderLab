"""Batch paper replay and evidence, with no automatic approval of unknown rules."""
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path

from .replay import Engine, digest, encode, json_line
from .strategy import LEG_LOTS, number
from .detection import instant


class Equity:
    """Tick-valued paper equity; no invented final liquidation or deal ordering."""
    def __init__(self):
        self.peak = Decimal(0)
        self.drawdown = Decimal(0)
        self.points = []

    def observe(self, engine, tick):
        if not engine.positions:
            return
        equity = engine.total_closed_profit
        contract = number(engine.config['contract_size'])
        for p in engine.positions:
            if p.open:
                side = 1 if p.plan.side == 'BUY' else -1
                quote = number(tick['bid' if side == 1 else 'ask'])
                equity += side*(quote-p.entry)*LEG_LOTS*contract-p.costs_paid
        self.peak = max(self.peak, equity)
        self.drawdown = max(self.drawdown, self.peak-equity)
        if not self.points or self.points[-1]['equity_change_usd'] != equity:
            self.points.append({'time': engine.now, 'input_order': engine.input_sequence,
                                'tick_index': tick.get('tick_index'), 'equity_change_usd': equity})


def results(engine, equity):
    counts = Counter(e['event'] for e in engine.events)
    entries = [e for e in engine.events if e['event'] == 'PAPER_ENTRY']
    exits = {e['position_id']: e for e in engine.events if e['event'] == 'PAPER_EXIT'}
    trades = []
    for entry in entries:
        closed = [exits[p] for p in entry['position_ids'] if p in exits]
        trades.append({'trade_id': entry['trade_id'], 'entry': entry, 'exits': closed,
                       'fully_closed': len(closed) == len(entry['position_ids']),
                       'realized_pnl_usd': sum((number(e['pnl_usd']) for e in closed), Decimal(0))})
    completed = [t for t in trades if t['fully_closed']]
    wins = sum(t['realized_pnl_usd'] > 0 for t in completed)
    losses = sum(t['realized_pnl_usd'] < 0 for t in completed)
    gross_wins=sum((t['realized_pnl_usd'] for t in completed if t['realized_pnl_usd']>0),Decimal(0))
    gross_losses=-sum((t['realized_pnl_usd'] for t in completed if t['realized_pnl_usd']<0),Decimal(0))
    reasons = Counter()
    opportunities = []
    for e in engine.events:
        if e['event'] in ('AUTO_SETUP_BLOCKED', 'CROSS_TIMEFRAME_RELATIONSHIP_BLOCKED',
                          'ENTRY_BLOCKED', 'BOS_REJECTED', 'BIG_CANDLE_REJECTED', 'FVG_REJECTED',
                          'EXECUTION_UNRESOLVED', 'BROKER_CONFIG_BLOCKED', 'CONFIG_UNRESOLVED'):
            opportunities.append(e)
            reasons.update(e.get('reasons', [e.get('reason', 'unspecified')]))
    report = {'event_counts': dict(sorted(counts.items())), 'automatic_valid_setups': counts['AUTO_SETUP_CONFIRMED'],
              'sourced_annotations': counts['SETUP_ANNOTATED'],
              'blocked_same_timeframe_relationships': counts['AUTO_SETUP_BLOCKED'],
              'blocked_cross_timeframe_relationships': counts['CROSS_TIMEFRAME_RELATIONSHIP_BLOCKED'],
              'rejection_reasons': dict(sorted(reasons.items())),
              'simulated_trades': len(trades), 'fully_closed_trades': len(completed),
              'open_legs': sum(p.open for p in engine.positions), 'wins': wins, 'losses': losses,
              'breakeven_trades': len(completed)-wins-losses,
              'performance_available': bool(trades),
              'win_rate': Decimal(wins)/len(completed) if completed else None,
              'profit_factor':gross_wins/gross_losses if gross_losses else None,
              'profit_factor_state':'DEFINED' if gross_losses else 'NO_LOSSES_UNBOUNDED' if gross_wins else 'NO_COMPLETED_TRADES',
              'realized_pnl_usd': engine.total_closed_profit if trades else None,
              'max_tick_equity_drawdown_usd': equity.drawdown if trades else None,
              'equity_valuation': 'observed Bid/Ask, paid entry commission; no hypothetical exit costs or swap',
              'trade_unit': 'one filled BOS entry (two 0.01-lot legs); paired entries counted separately',
              'blocked_reason_unit': 'diagnostic event, not unique tradable opportunity',
              'trades': trades, 'opportunities': opportunities}
    return report


def batch(paths, config_path, output, allow_annotations=False):
    paths = [Path(p) for p in paths]
    if not paths or len({p.resolve() for p in paths}) != len(paths):
        raise ValueError('Supply distinct independent input files; duplicate captures would double-count results')
    if output.exists():
        raise ValueError('Output already exists; choose a fresh directory')
    config = json.loads(config_path.read_text(encoding='utf-8'), parse_float=Decimal)
    if config.get('broker_execution_enabled') is not False:
        raise ValueError('Batch replay requires broker_execution_enabled=false')
    output.mkdir(parents=True)
    reports = []
    for case, path in enumerate(paths, 1):
        engine, equity = Engine(config), Equity()
        counts = Counter()
        error = None
        index = 0
        offsets=set(); startup_delivery=None
        try:
            with path.open(encoding='utf-8-sig') as stream:
                for index, line in enumerate(stream, 1):
                    if not line.strip():
                        continue
                    row = json.loads(line, parse_float=Decimal)
                    if not allow_annotations and row['kind'] not in ('bar', 'tick'):
                        raise ValueError('Market-only mode rejects annotations; opt in explicitly for sourced simulation')
                    engine.accept(row)
                    offset=row.get('server_utc_offset_seconds')
                    if isinstance(offset,int) and not isinstance(offset,bool): offsets.add(offset)
                    if row['kind']=='bar' and startup_delivery is None:
                        startup_delivery=instant(row['time'])
                    counts[row['kind']] += 1
                    if row['kind'] == 'tick':
                        equity.observe(engine, row)
        except (ValueError, KeyError, TypeError, OSError) as exception:
            error = f'Input line {index}: {exception}'
        case_out = output / f'case-{case:03d}'
        case_out.mkdir()
        if error is None:
            from .candidates import write_candidates
            write_candidates(engine,case_out,next(iter(offsets)) if len(offsets)==1 else None,startup_delivery)
        journal = ''.join(json_line(e) for e in engine.events)
        (case_out / 'events.jsonl').write_text(journal, encoding='utf-8', newline='\n')
        report = {'status': 'REJECTED' if error else 'ACCEPTED', 'error': error,
                  'input': str(path.resolve()), 'input_sha256': digest(path) if path.is_file() else None,
                  'input_mode': 'sourced_annotation_simulation' if allow_annotations else 'market_only',
                  'automatic_execution_approved': False, 'inputs_processed': dict(counts),
                  'journal_sha256': digest(case_out / 'events.jsonl'),
                  'results': results(engine, equity) if error is None else None}
        (case_out / 'report.json').write_text(json.dumps(encode(report), sort_keys=True, indent=2)+'\n', encoding='utf-8')
        (case_out / 'equity.jsonl').write_text(''.join(json_line(p) for p in equity.points) if error is None else '', encoding='utf-8')
        reports.append(report)
    accepted = [r['results'] for r in reports if r['results'] is not None]
    closed = sum(r['fully_closed_trades'] for r in accepted)
    trades = sum(r['simulated_trades'] for r in accepted)
    wins = sum(r['wins'] for r in accepted)
    summary = {'mode': 'independent_paper_cases_no_state_carried_between_files',
               'broker_execution_enabled': False, 'config_sha256': digest(config_path),
               'spec_sha256': digest(Path(__file__).parent.parent / 'docs/sources/canonical-strategy.fa.md'),
               'code_sha256': {p.name: digest(p) for p in sorted(Path(__file__).parent.glob('*.py'))},
               'cases': reports, 'accepted_cases': len(accepted), 'rejected_cases': len(reports)-len(accepted),
               'historical_automatic_trades': sum(r['simulated_trades'] for r in reports_results(reports, 'market_only')),
               'simulated_trades': trades, 'fully_closed_trades': closed,
               'performance_available': bool(trades), 'win_rate': Decimal(wins)/closed if closed else None,
               'realized_pnl_usd': sum((r['realized_pnl_usd'] or Decimal(0) for r in accepted), Decimal(0)) if trades else None,
               'drawdown_scope': 'per case only; independent cases are not a chronological portfolio',
               'automatic_demo_ready': False}
    (output / 'batch.json').write_text(json.dumps(encode(summary), sort_keys=True, indent=2)+'\n', encoding='utf-8')
    return summary


def reports_results(reports, mode):
    return [r['results'] for r in reports if r['input_mode'] == mode and r['results'] is not None]
