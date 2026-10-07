"""Source guards only; native JSON generation checks run in StrategyChecks.mq5."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class NativeLogContractChecks(unittest.TestCase):
    def test_bos_and_big_candle_share_numeric_epoch_serialization(self):
        source = (ROOT / "mt5/Include/TraderLab/Detection.mqh").read_text(encoding="utf-8")
        self.assertIn('(string)(long)value', source)
        self.assertEqual(source.count('candidate_server_epoch'), 1)
        self.assertEqual(source.count('TLCandidateEpoch('), 3)  # definition, BOS, Big Candle/FVG
        self.assertIn('TLCandidateEpoch(c.time)', source)
        self.assertIn('TLCandidateEpoch(history[10].time)', source)
        self.assertNotIn('(string)c.time', source)
        self.assertNotIn('(string)history[10].time', source)

    def test_native_logger_distinguishes_default_seconds_from_explicit_milliseconds(self):
        source = (ROOT / "mt5/Include/TraderLab/EventLog.mqh").read_text(encoding="utf-8")
        self.assertIn('const int millis=-1', source)
        self.assertIn('string precision=(millis<0)?"seconds":"milliseconds";', source)
        self.assertIn('int fraction=(millis<0)?0:millis;', source)
        self.assertIn('timestamp_precision', source)


if __name__ == "__main__":
    unittest.main()
