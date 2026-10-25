"""Native integration boundaries and real-candle no-lookahead regression."""
import json
from pathlib import Path
import unittest

from traderlab.detection import Bar, Detector, instant

ROOT = Path(__file__).resolve().parents[1]


class NativeBosAge(unittest.TestCase):
    def test_policy_is_tester_only_opt_in_and_before_pending_or_broker(self):
        ea = (ROOT/'mt5/TraderLab.mq5').read_text()
        controller = (ROOT/'mt5/Include/TraderLab/CoreController.mqh').read_text()
        policy = (ROOT/'mt5/Include/TraderLab/FirstTouchPolicy.mqh').read_text()
        namespace = (ROOT/'mt5/Include/TraderLab/AutoCoreTrial.mqh').read_text()
        self.assertIn('InpExperimentalM1MaxAgeMinutes=0', ea)
        self.assertIn('!TLPolicyActive() || InpExperimentalAutoCoreTester==0', ea)
        self.assertIn('minutes!=60 && minutes!=120', policy)
        self.assertIn('if(frame!=0) return true', policy)
        ret = controller[controller.index('void ExperimentalReturn'):controller.index('void PanelControl')]
        self.assertLess(ret.index('else if(!age_allowed)'), ret.index('ArrayResize(pending'))
        dispatch = controller[controller.index('string reason=TLCoreEntryBlock(g,gaps[p.gap]'):]
        self.assertLess(dispatch.index('TLTesterBosAgeAllowed'), dispatch.index('book.Begin('))
        self.assertIn(':m1age', namespace)
        self.assertIn('TL_TESTER_M1_MAX_AGE_MINUTES>0', namespace)
        tracker = (ROOT/'mt5/Include/TraderLab/Retests.mqh').read_text()
        self.assertNotIn('TL_TESTER_M1_MAX_AGE_MINUTES', tracker)
        self.assertIn('Archive retained, no expiry or history reset', tracker)

    def test_2016_return_precedes_even_fvg_geometry_and_remains_blocked(self):
        evidence = json.loads((ROOT/'docs/reports/owner-bos-20261019/evidence.json').read_text())
        candle = instant('2026-10-13T18:06:00Z')
        first_return = instant('2026-10-13T18:06:16.085Z')
        confirmation = instant('2026-10-13T18:17:00.154Z')
        detector = Detector()
        found = []
        for row in evidence['closed_m1_window']:
            available = instant(row['time'])
            for e in detector.accept(Bar.read(row)):
                if e.get('candidate_at') == candle and e['event'] in ('BIG_CANDLE_CONFIRMED', 'FVG_CONFIRMED'):
                    found.append(e)
                    self.assertGreater(available, first_return)
                    self.assertGreaterEqual(available, confirmation)
        self.assertEqual({e['event'] for e in found}, {'BIG_CANDLE_CONFIRMED', 'FVG_CONFIRMED'})
        fvg = next(e for e in found if e['event'] == 'FVG_CONFIRMED')
        self.assertEqual(fvg['formation_at'], instant('2026-10-13T18:08:00.142Z'))
        self.assertEqual(fvg['available_at'], confirmation)


if __name__ == '__main__':
    unittest.main()
