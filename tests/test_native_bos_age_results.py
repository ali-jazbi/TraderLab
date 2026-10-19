"""Committed NEW native Tester deals, not retrospective removal of old positions."""
from decimal import Decimal as D
import json
from pathlib import Path
import unittest

from tools.report_bos_age_study import deal_signature, verify_actual_ages

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT/'docs/reports/native-bos-age-20261019'


class NativeAgeResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runs, cls.performance = {}, {}
        for window in ('training', 'holdout'):
            for r, p in zip(json.loads((REPORT/window/'results.json').read_text()),
                            json.loads((REPORT/window/'performance.json').read_text())):
                cap = int(r['inputs']['InpExperimentalM1MaxAgeMinutes'])
                cls.runs[window, cap] = r
                cls.performance[window, cap] = p

    def verification(self, window, cap):
        return json.loads((REPORT/window/f'AGE{cap}/verification.json').read_text())

    def test_six_new_native_runs_all_actual_deals_reconcile_in_fixed_windows(self):
        self.assertEqual(len(self.runs), 6)
        self.assertEqual(len({r['compiled_binary_sha256'] for r in self.runs.values()}), 1)
        for key, r in self.runs.items():
            self.assertEqual(r['native_report_metrics']['History Quality:'], '100% real ticks')
            self.assertEqual(r['inputs']['InpRequestCoreDemoExecution'], 'false')
            self.assertTrue(r['all_actual_deals_inside_window'])
            p = self.performance[key]
            self.assertEqual(r['actual_closed_positions'], p['position_performance']['count'])
            self.assertEqual(r['actual_entry_deals'], r['actual_closed_positions'])
            self.assertEqual(r['actual_closed_positions'], int(r['native_report_metrics']['Total Trades:']))
            self.assertEqual(D(r['deal_net_reconciled']), D(p['position_performance']['net']))
            self.assertLessEqual(D(p['maximum_actual_open_lots']), D('.04'))
            capture = next(e for e in r['events'] if e['event'] == 'TICK_CAPTURE_SUMMARY')
            self.assertFalse(capture['capture_halted'])
            self.assertTrue(capture['terminal_cursor_evidence_valid'])
            self.assertEqual(capture['cursor_ambiguities'], 0)
            self.assertEqual(capture['copyticks_errors'], 0)

    def test_age0_reproduces_original_deals_and_no_other_input_changed(self):
        for window in ('training', 'holdout'):
            old = json.loads((ROOT/f'docs/reports/auto-core-discovery-20261018/final-{window}/results.json').read_text())[0]
            self.assertEqual(deal_signature(self.runs[window, 0]), deal_signature(old))
            for cap in (0, 60, 120):
                actual = self.runs[window, cap]['inputs']
                excluded = {'InpLogFile', 'InpExperimentalM1MaxAgeMinutes'}
                self.assertEqual({k:v for k,v in actual.items() if k not in excluded},
                                 {k:v for k,v in old['inputs'].items() if k not in excluded})
                v = self.verification(window, cap)
                self.assertTrue(v['calendar']['warmup_and_measured_days_identical'])
                self.assertTrue(v['calendar']['all_news_identical'])

    def test_expired_m1_never_fills_but_higher_timeframes_are_not_expired(self):
        late = {'M1:BUY:2026-10-13T17:49:00+00:00', 'M1:BUY:2026-10-16T04:07:00+00:00'}
        baseline_ids = {p['bos_id'] for p in self.verification('holdout', 0)['submitted_ages']}
        self.assertTrue(late <= baseline_ids)
        for (window, cap), r in self.runs.items():
            verified = verify_actual_ages(r, self.performance[window, cap])
            if cap:
                self.assertFalse(late & {p['bos_id'] for p in verified})
                self.assertTrue(all(p['age_ms'] <= cap*60000 for p in verified if p['timeframe'] == 'M1'))
                if window == 'training':
                    self.assertTrue(any(p['timeframe'] in ('M5', 'M15') and p['age_ms'] > 7200000 for p in verified))

    def test_market_detection_grouping_and_consumption_history_are_preserved(self):
        for window in ('training', 'holdout'):
            base = self.verification(window, 0)
            for cap in (60, 120):
                v = self.verification(window, cap)
                self.assertEqual(v['market'], base['market'])
                self.assertEqual(v['structural_sha256'], base['structural_sha256'])
                self.assertEqual(v['counts'], base['counts'])
                self.assertGreater(len(v['first_return_age_rejections']), 0)
                self.assertTrue(all(not r['signal_ready'] and not r['age_allowed'] for r in v['first_return_age_rejections']))

    def test_fast_2016_bos_still_blocked_for_fvg_not_age_or_hindsight(self):
        key = 'M1:BUY:2026-10-13T17:16:00+00:00'
        for cap in (0, 60, 120):
            events = self.verification('holdout', cap)['owner2016_events']
            returned = next(e for e in events if e['event'] == 'EXPERIMENTAL_FIRST_RETURN')
            self.assertEqual(returned['server_time'], '2026-10-13T21:06:16.085')
            self.assertEqual(returned['bos_age_ms'], 3016085)
            self.assertTrue(returned['age_allowed'])
            self.assertEqual(returned['reason'], 'NO_ACTIVE_EXPERIMENTAL_GROUP')
            self.assertTrue(any(e['event'] == 'CORE_BOS_CONFIRMED' for e in events))
            self.assertFalse(any(p['bos_id'] == key for p in self.verification('holdout', cap)['submitted_ages']))
        older = json.loads((REPORT/'owner2016-prior-packages.json').read_text())
        self.assertEqual(len(older['prior_geometric_relations']), 19)
        self.assertTrue(older['all_prior_relations_full'])
        self.assertTrue(all(r['fill_state'] == 'FULL' and r['time'] <= older['first_return_utc']
                            for r in older['prior_geometric_relations']))


if __name__ == '__main__':
    unittest.main()
