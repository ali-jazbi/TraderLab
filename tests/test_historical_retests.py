"""Genuine sparse market excerpts: chronology, not synthetic historical trades."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import unittest

from traderlab.replay import Engine
from traderlab.retests import FirstReturn
from traderlab.retests import HistoricalRetests
from traderlab.detection import Bar

ROOT = Path(__file__).resolve().parents[1]


class HistoricalRetestChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / 'tests/fixtures/oct07-retest-market.jsonl'
        manifest = json.loads(path.with_suffix('.provenance.json').read_text(encoding='utf-8'))
        assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest['fixture_sha256']
        cls.rows = [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]
        cfg = json.loads((ROOT / 'configs/production.template.json').read_text(encoding='utf-8'))
        # Explicit chart-price diagnostic lane, not approval of executable quote policy.
        cfg['observation_price_side'] = 'bid'
        cls.engine = Engine(cfg)
        for row in cls.rows:
            cls.engine.accept(row)

    def history(self, timeframe, side, candidate):
        return self.engine.retests.histories[f'{timeframe}:{side}:{candidate}+00:00']

    def test_m1_break_and_first_returns_precede_closed_bar_logging(self):
        h = self.history('M1', 'BUY', '2026-10-07T03:10:00')
        lane = h.lanes['bid']
        self.assertEqual(lane['break_at'].isoformat(), '2026-10-07T03:25:50.736000+00:00')
        ask = lane['returns']['ask'].result
        bid = lane['returns']['bid'].result
        self.assertEqual(ask['first_return_at'].isoformat(), '2026-10-07T03:25:58.051000+00:00')
        self.assertEqual((ask['previous_quote'], ask['observed_quote']), (Decimal('4142.33'), Decimal('4142.30')))
        self.assertEqual(ask['tick_index'], 44210)
        self.assertFalse(ask['exact_quote'])
        self.assertEqual(bid['first_return_at'].isoformat(), '2026-10-07T03:28:51.731000+00:00')
        self.assertTrue(bid['exact_quote'])
        confirmed = next(e for e in self.engine.events if e['event'] == 'BOS_CONFIRMED'
                         and e['timeframe'] == 'M1' and e['side'] == 'BUY'
                         and e['candidate_at'] == '2026-10-07T03:10:00Z')
        self.assertEqual(confirmed['time'], '2026-10-07T03:26:00.798000Z')
        self.assertTrue(confirmed['intrabar_history']['bid']['returns']['ask']['consumed'])

    def test_m5_mirrored_returns_are_not_outbound_crossings(self):
        lane = self.history('M5', 'SELL', '2026-10-07T02:05:00').lanes['bid']
        self.assertEqual(lane['break_at'].isoformat(), '2026-10-07T03:06:25.538000+00:00')
        for quote, stamp, index, previous, current in (
                ('bid', '2026-10-07T03:12:53.153000+00:00', 42417, '4139.71', '4139.84'),
                ('ask', '2026-10-07T03:12:47.038000+00:00', 42401, '4139.73', '4139.79')):
            result = lane['returns'][quote].result
            self.assertEqual(result['first_return_at'].isoformat(), stamp)
            self.assertEqual(result['tick_index'], index)
            self.assertEqual((result['previous_quote'], result['observed_quote']), (Decimal(previous), Decimal(current)))
            self.assertFalse(result['exact_quote'])

    def test_late_fvg_confirmation_carries_consumed_history_without_promotion(self):
        pairs = [e for e in self.engine.events if e['event'] == 'AUTO_SETUP_BLOCKED']
        for key, fvg_at in (('M1:BUY:2026-10-07T03:10:00+00:00', '2026-10-07T03:36:00.045000Z'),
                            ('M5:SELL:2026-10-07T02:05:00+00:00', '2026-10-07T05:25:01.010000Z')):
            pair = next(e for e in pairs if e['bos_id'] == key and e['fvg_available_at'] == fvg_at)
            self.assertIn('FIRST_RETURN_CONSUMED_BEFORE_FVG_CONFIRMATION', pair['reasons'])
            self.assertTrue(pair['intrabar_history']['bid']['returns']['ask']['consumed'])
            self.assertTrue(pair['diagnostic_only'])
        self.assertFalse(self.engine.positions)
        self.assertFalse(self.engine.setups)
        # The 07:07 exact Ask return cannot produce a second first-return event.
        returns = [e for e in self.engine.events if e['event'] == 'BOS_FIRST_DIRECTIONAL_RETURN'
                   and e['bos_id'] == 'M1:BUY:2026-10-07T03:10:00+00:00' and e['retest_quote'] == 'ask']
        self.assertEqual(len(returns), 1)

    def test_equal_millisecond_occurrences_preserve_one_consumed_return(self):
        state = FirstReturn('BUY', Decimal('4142.32'))
        at = datetime(2026, 10, 7, tzinfo=timezone.utc)
        self.assertIsNone(state.advance(Decimal('4142.33'), at, 1, 1))
        result = state.advance(Decimal('4142.30'), at, 2, 2)
        self.assertFalse(result['exact_quote'])
        self.assertIsNone(state.advance(Decimal('4142.32'), at, 3, 3))
        self.assertEqual(state.result['tick_index'], 2)

    def test_unknown_quote_policy_keeps_separate_diagnostics(self):
        cfg = json.loads((ROOT / 'configs/production.template.json').read_text(encoding='utf-8'))
        cfg["observation_price_side"]=None
        engine = Engine(cfg)
        for row in self.rows:
            engine.accept(row)
        h = engine.retests.histories['M1:BUY:2026-10-07T03:10:00+00:00']
        self.assertEqual(set(h.lanes), {'bid', 'ask'})
        self.assertFalse(engine.positions)
        self.assertFalse(engine.setups)

    def test_late_annotation_shares_history_and_cannot_rearm_return(self):
        cfg = json.loads((ROOT / 'configs/fixture.example.json').read_text(encoding='utf-8'))
        cfg['symbol_aliases'] = {'XAUUSD_o': 'XAUUSD'}
        engine = Engine(cfg)
        for row in self.rows:
            if row['time'] <= '2026-10-07T03:36:00.045Z':
                engine.accept(row)
        key = 'M1:BUY:2026-10-07T03:10:00+00:00'
        historical = engine.retests.histories[key].lanes['bid']['returns']['ask']
        engine.accept({'kind': 'setup', 'symbol': 'XAUUSD_o', 'time': '2026-10-07T03:36:00.045Z',
                       'setup_id': 'unit-late-link', 'side': 'BUY', 'confirmed': True,
                       'source': 'UNIT ONLY asserted association; not historical trading approval',
                       'fill_state': 'PARTIAL', 'fvg': ['4139.60', '4142.19'],
                       'ob': ['4142.19', '4143.85'],
                       'bos': [{'id': key, 'level': '4141.82', 'zone': ['4141.82', '4141.82']}]})
        self.assertIs(engine.core_returns[key], historical)
        actual = next(r for r in self.rows if r['server_time'] == '2026-10-07T07:07:18.392')
        engine.accept(actual)
        self.assertIn(key, engine.consumed_bos)
        self.assertFalse(engine.positions)
        self.assertTrue(any(e.get('reason') == 'FIRST_RETEST_CONSUMED_BEFORE_SETUP_AVAILABLE'
                            for e in engine.events))

    def test_break_before_qualification_cannot_be_rehabilitated(self):
        tracker = HistoricalRetests('bid')
        candidate = Bar.read(next(r for r in self.rows if r.get('timeframe') == 'M1'
                                 and r['opened_at'] == '2026-10-07T03:10:00.000Z'))
        tracker.accept_bar(candidate, [])
        key = tracker.identity('M1', 'BUY', candidate.opened)
        tracker.accept_tick({'bid': '4142', 'ask': '4142.22'}, candidate.available, 1)
        qualifier = Bar.read(next(r for r in self.rows if r.get('timeframe') == 'M1'
                                  and r['opened_at'] == '2026-10-07T03:12:00.000Z'))
        tracker.accept_bar(qualifier, [{'event': 'BOS_CANDIDATE_QUALIFIED', 'side': 'BUY',
                                       'timeframe': 'M1', 'candidate_at': candidate.opened}])
        self.assertEqual(tracker.snapshot(key)['bid']['state'], 'BLOCKED')
        self.assertEqual(tracker.snapshot(key)['bid']['reason'], 'tick_break_before_qualification')
        events = tracker.accept_tick({'bid': '4142.10', 'ask': '4142.32'}, qualifier.available, 2)
        self.assertFalse(any(e['bos_id'] == key for e in events))


if __name__ == '__main__':
    unittest.main()
