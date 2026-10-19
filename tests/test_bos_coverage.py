"""Both owner-requested candles survive independently in genuine native history."""
import csv
import json
from decimal import Decimal as D
from pathlib import Path
import unittest

from tools.dump_bos_coverage import coverage

REPORT = Path(__file__).resolve().parents[1]/'docs/reports/bos-coverage-20261019'
HIGHER = 'M1:BUY:2026-10-13T17:16:00+00:00'
LOWER = 'M1:BUY:2026-10-13T17:49:00+00:00'


class BosCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads((REPORT/'evidence.json').read_text(encoding='utf-8'))
        cls.rows = coverage(cls.evidence)
        cls.by_id = {r['bos_id']: r for r in cls.rows}

    def test_every_closed_candle_retains_both_sides_without_group_filter(self):
        self.assertEqual(len(self.rows), 140)
        self.assertEqual(len(self.by_id), 140)
        self.assertEqual(sum(r['side'] == 'BUY' for r in self.rows), 70)
        self.assertEqual(sum(r['side'] == 'SELL' for r in self.rows), 70)
        self.assertTrue(all(r['detector_merge_dedup_rule'] == 'NONE' for r in self.rows))

    def test_higher_and_lower_are_both_native_and_python_accepted(self):
        for key, high, low, qclose, qualification in (
            (HIGHER, '4157.84', '4156.88', '4156.48', '20:17'),
            (LOWER, '4153.01', '4150.14', '4149.79', '20:50'),
        ):
            row = self.by_id[key]
            self.assertEqual(row['status'], 'ACCEPTED')
            self.assertEqual(row['native_status'], 'ACCEPTED')
            self.assertEqual(D(row['wick_level']), D(high))
            self.assertEqual(D(row['low']), D(low))
            self.assertEqual(D(row['qualification_close']), D(qclose))
            self.assertLess(D(row['qualification_close']), D(row['low']))
            self.assertEqual(row['qualification_candle_server'][11:16], qualification)
            self.assertEqual(row['reject_reason'], '')
        self.assertEqual(self.by_id[HIGHER]['intrabar_bid_break_server'], '2026-10-13T21:06:14.585')
        self.assertEqual(self.by_id[LOWER]['intrabar_bid_break_server'], '2026-10-13T21:05:59.302')

    def test_rejected_opposite_seed_not_hidden_or_promoted(self):
        opposite = self.by_id[HIGHER.replace(':BUY:', ':SELL:')]
        self.assertEqual(opposite['status'], 'REJECTED')
        self.assertEqual(opposite['reject_reason'], 'break_before_qualification')
        self.assertEqual(opposite['qualification_candle_server'], '')
        self.assertTrue(all(r['native_status'] == r['status'] for r in self.rows))

    def test_consumption_is_downstream_not_loss_of_detection(self):
        row = self.by_id[HIGHER]
        self.assertEqual(row['first_bid_return_server'], '2026-10-13T21:06:16.085')
        self.assertIn('FIRST_RETURN_CONSUMED_BEFORE_FVG_CONFIRMATION', row['package_relation_reasons'])
        groups = self.evidence['related_groups']
        self.assertEqual(len(groups), 2)
        self.assertTrue(all(HIGHER not in g['selected_bos_ids'].split(';') for g in groups))
        self.assertTrue(any(LOWER in g['selected_bos_ids'].split(';') for g in groups))
        self.assertEqual(row['status'], 'ACCEPTED')

    def test_checked_in_csv_is_exact_unfiltered_replay(self):
        with (REPORT/'candidates.csv').open(encoding='utf-8-sig', newline='') as source:
            self.assertEqual(list(csv.DictReader(source)), self.rows)


if __name__ == '__main__':
    unittest.main()
