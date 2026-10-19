"""Owner-labelled screenshots and genuine native evidence; no inferred feed labels."""
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import unittest

from tools.audit_owner_bos import ROBOT, POSITIVE_PROXY, NEGATIVE_PROXY, GAPS, at
from traderlab.detection import Bar, Detector
from traderlab.retests import FirstReturn

ROOT = Path(__file__).resolve().parents[1]


class OwnerBosEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads((ROOT/'docs/reports/owner-bos-20261019/evidence.json').read_text())

    def test_owner_positive_negative_labels_preserved_without_feed_transfer(self):
        f = self.evidence['feedback']
        self.assertEqual(f['positive']['label'], 'OWNER_CONFIRMED_BOS')
        self.assertEqual(f['negative']['label'], 'NOT_BOS')
        self.assertIsNone(f['source_timezone']); self.assertIsNone(f['source_broker'])
        for side in ('positive', 'negative'):
            image = f[side]['image']
            self.assertEqual(hashlib.sha256((ROOT/image['path']).read_bytes()).hexdigest(), image['sha256'])
            self.assertEqual(f[side]['native_label_transfer'], 'UNRESOLVED_FEED_MATCH')
        a = self.evidence['alignment']
        self.assertFalse(a['timezone_confirmed']); self.assertFalse(a['price_equivalence_confirmed'])
        self.assertEqual(a['exact_joint_matches'], 0)

    def test_clock_name_does_not_override_real_ohlc(self):
        case = self.evidence['cases'][ROBOT]
        self.assertEqual(case['candle']['opened_at'], '2026-10-13T17:49:00.000Z')
        self.assertEqual(D(case['candle']['high']), D('4153.01'))
        self.assertNotEqual(D(case['candle']['high']), D(self.evidence['feedback']['negative']['ohlc']['high']))
        self.assertEqual(self.evidence['server_utc_offset_seconds'], 10800)
        self.assertEqual(self.evidence['iran_utc_offset_seconds'], 12600)
        for c in self.evidence['cases'].values(): self.assertTrue(c['tick_ohlc_verified'])

    def test_actual_robot_passes_only_the_documented_qualification_predicate(self):
        c = self.evidence['cases'][ROBOT]
        self.assertLess(D(c['qualification_candle']['close']), D(c['candle']['low']))
        self.assertEqual(D(c['qualification_candle']['close']), D('4149.79'))
        self.assertEqual(c['owner_label_transfer'], 'NOT_PERMITTED_WITHOUT_FEED_MATCH')
        native = [e for e in c['events'] if e['event'] == 'BOS_FIRST_DIRECTIONAL_RETURN'
                  and e['break_quote'] == e['retest_quote'] == 'bid'][0]
        self.assertFalse(native['exact_quote'])
        self.assertEqual(native['server_time'], '2026-10-14T04:00:01.473')
        self.assertEqual(D(self.evidence['actual_dispatch']['actual_signal_quote']['ask']), D('4153.64'))

    def test_positive_proxy_was_detected_and_consumed_before_availability(self):
        events = self.evidence['cases'][POSITIVE_PROXY]['events']
        first = next(e for e in events if e['event'] == 'BOS_FIRST_DIRECTIONAL_RETURN'
                     and e['break_quote'] == e['retest_quote'] == 'bid')
        relation = next(e for e in events if e['event'] == 'CORE_SETUP_CANDIDATE' and e['fvg_id'] == GAPS[1])
        self.assertEqual(first['server_time'], '2026-10-13T21:06:16.897')
        self.assertTrue(first['exact_quote'])
        self.assertLess(at(first['time']), at(relation['formation_at']))
        self.assertLess(at(relation['formation_at']), at(relation['fvg_available_at']))
        self.assertIn('FIRST_RETURN_CONSUMED_BEFORE_FVG_CONFIRMATION', relation['reasons'])

    def test_python_closed_bar_diagnostics_reproduce_the_three_native_cases(self):
        detector = Detector(); records = []
        for row in self.evidence['closed_m1_window']: records.extend(detector.accept(Bar.read(row)))
        for key, expected in ((ROBOT, 'BOS_CONFIRMED'), (POSITIVE_PROXY, 'BOS_CONFIRMED'), (NEGATIVE_PROXY, 'BOS_REJECTED')):
            selected = [e for e in records if e.get('side') == 'BUY' and e.get('candidate_at') == at(key.split(':', 2)[2])
                        and e['event'] in ('BOS_CONFIRMED', 'BOS_REJECTED')]
            self.assertEqual(len(selected), 1); self.assertEqual(selected[0]['event'], expected)

    def test_actual_quote_transitions_replay_without_rearming_or_fills(self):
        for key in (ROBOT, POSITIVE_PROXY):
            c = self.evidence['cases'][key]
            native = next(e for e in c['events'] if e['event'] == 'BOS_FIRST_DIRECTIONAL_RETURN'
                          and e['break_quote'] == e['retest_quote'] == 'bid')
            state = FirstReturn('BUY', D(native['entry_reference'])); found = []
            for t in c['local_return_tick_window']:
                event = state.advance(D(t['bid']), t['time'], t['tick_index'], t['tick_index'])
                if event: found.append(event)
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]['first_return_at'], native['time'])
            self.assertEqual(found[0]['tick_index'], native['tick_index'])
            self.assertEqual(found[0]['previous_quote'], D(native['previous_quote']))
            self.assertEqual(found[0]['exact_quote'], native['exact_quote'])


if __name__ == '__main__': unittest.main()
