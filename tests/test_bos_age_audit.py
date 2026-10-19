"""Owner qualitative age amendment, actual deal evidence and fixed offline studies."""
from collections import Counter
import csv
from decimal import Decimal as D
import gzip
import json
from pathlib import Path
import unittest

from tools.audit_bos_age import age_allowed, age_ms, cohorts, entries

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT/'docs/reports/bos-age-20261019'


class BosAgeAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads((REPORT/'evidence.json').read_text())
        cls.summary = json.loads((REPORT/'summary.json').read_text())
        cls.positions = entries(cls.evidence)
        cls.bos = {b['bos_id']: b for b in cls.evidence['bos']}

    def test_exact_study_boundaries_and_real_milliseconds(self):
        candle = '2026-10-13T17:49:00+00:00'
        for cap, boundary in ((60, '18:49'), (120, '19:49')):
            self.assertTrue(age_allowed('M1', candle, f'2026-10-13T{boundary}:00.000Z', cap))
            self.assertFalse(age_allowed('M1', candle, f'2026-10-13T{boundary}:00.001Z', cap))
        self.assertFalse(age_allowed('M1', candle, '2026-10-13T17:48:59.999Z', 120))
        with self.assertRaises(ValueError):
            age_allowed('M1', candle, candle, 90)

    def test_no_arbitrary_expiry_for_other_timeframes_or_unchanged_policy(self):
        for tf in ('M5', 'M15', 'H1', 'H4'):
            self.assertTrue(age_allowed(tf, '2026-10-01T00:00:00Z', '2026-10-16T00:00:00Z', 60))
        self.assertTrue(age_allowed('M1', '2026-10-01T00:00:00Z', '2026-10-16T00:00:00Z', 0))

    def test_exact_14_and_16_october_delays_from_candle_not_fvg(self):
        for key, delay in (('M1:BUY:2026-10-13T17:49:00+00:00', 25861473),
                           ('M1:BUY:2026-10-16T04:07:00+00:00', 14114047)):
            b = self.bos[key]
            self.assertEqual(age_ms(b['candidate_at'], b['first_bid_touch_at']), delay)
            pair = [p for p in self.positions if p['bos_id'] == key]
            self.assertEqual(len(pair), 2)
            for p in pair:
                self.assertEqual(D(p['age_at_touch_minutes']), D(p['age_at_entry_minutes']))
                self.assertFalse(p['allowed_60']); self.assertFalse(p['allowed_120'])
        pair = [p for p in self.positions if p['bos_id'] == 'M1:BUY:2026-10-13T17:49:00+00:00']
        self.assertEqual(sum(D(p['net']) for p in pair), D('-8.38'))

    def test_fast_higher_bos_is_not_an_age_reject_and_is_not_retroactively_filled(self):
        key = 'M1:BUY:2026-10-13T17:16:00+00:00'
        b = self.bos[key]
        self.assertEqual(age_ms(b['candidate_at'], b['first_bid_touch_at']), 3016085)
        self.assertTrue(age_allowed('M1', b['candidate_at'], b['first_bid_touch_at'], 60))
        relation = next(r for r in self.evidence['relations'] if r['bos_id'] == key and
                        r['fvg_id'] == 'M1:BUY:2026-10-13T18:06:00+00:00')
        self.assertLess(b['first_bid_touch_at'], relation['formation_at'])
        self.assertIn('FIRST_RETURN_CONSUMED_BEFORE_FVG_CONFIRMATION', relation['reasons'])
        self.assertFalse(any(p['bos_id'] == key for p in self.positions))
        self.assertEqual(b['structural_status'], 'CONFIRMED')

    def test_fixed_studies_remove_winners_and_losers(self):
        rows = cohorts(self.positions)
        summary = {(r['window'], r['experiment']): r for r in rows}
        train = summary['final-training', 'EXPERIMENTAL_M1_AGE_120']['removed_positions']
        self.assertEqual((train['wins'], train['losses'], D(train['net'])), (2, 2, D('7.55')))
        hold = summary['final-holdout', 'EXPERIMENTAL_M1_AGE_120']['removed_positions']
        self.assertEqual((hold['wins'], hold['losses'], D(hold['net'])), (0, 4, D('-16.72')))
        self.assertEqual(rows, self.summary['cohort_comparisons'])
        self.assertTrue(all(r['causal_backtest_performance'] is None and r['equity_drawdown'] is None for r in rows))

    def test_actual_entry_ledger_reproduces_without_new_fills(self):
        with (REPORT/'actual-entry-ages.csv').open(encoding='utf-8-sig', newline='') as source:
            recorded = list(csv.DictReader(source))
        self.assertEqual(recorded, [{k:str(v) for k,v in p.items()} for p in self.positions])
        self.assertEqual(len(self.positions), 32)
        self.assertEqual(sum(p['leg'] == 1 and p['timeframe'] == 'M1' for p in self.positions), 11)
        self.assertEqual(sum(p['leg'] == 1 and not p['allowed_120'] for p in self.positions), 4)

    def test_complete_archive_keeps_old_structurally_confirmed_bos(self):
        with gzip.open(REPORT/'all-qualified-bos.csv.gz', 'rt', encoding='utf-8-sig', newline='') as source:
            rows = list(csv.DictReader(source))
        self.assertEqual(len(rows), 24970)
        self.assertEqual(len({r['bos_id'] for r in rows}), 24970)
        self.assertEqual(dict(Counter(r['timeframe'] for r in rows)), self.summary['qualified_by_timeframe'])
        old = next(r for r in rows if r['bos_id'] == 'M1:BUY:2026-10-13T17:49:00+00:00')
        self.assertEqual(old['structural_status'], 'CONFIRMED')
        self.assertIn('2026-10-14T04:00:01.473', old['actual_entries'])

    def test_age_study_is_not_mislabelled_as_new_oos_or_execution_approval(self):
        self.assertEqual(self.summary['automatic_demo'], 'LOCKED')
        self.assertFalse(self.summary['production_numerical_expiry_implemented'])
        self.assertIn('already inspected', self.summary['unseen_validation'])
        self.assertEqual([s['age_blocked'] for s in self.summary['signal_comparisons']], [7, 5, 6, 5])


if __name__ == '__main__':
    unittest.main()
