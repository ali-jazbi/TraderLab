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

    def test_native_capture_has_one_history_path_and_separate_detection(self):
        ea = (ROOT / "mt5/TraderLab.mq5").read_text(encoding="utf-8")
        capture = (ROOT / "mt5/Include/TraderLab/TickCapture.mqh").read_text(encoding="utf-8")
        ontick = ea.split('void OnTick()', 1)[1].split('void ProcessClosedBars()', 1)[0]
        self.assertIn('tick_capture.OnCallback(event_log)', ontick)
        self.assertNotIn('CopyRates', ontick)
        self.assertNotIn('SymbolInfoTick', ontick)
        self.assertEqual(capture.count('int count=CopyTicksRange('), 1)
        self.assertIn('COPY_TICKS_ALL,(ulong)from_msc,(ulong)to_msc', capture)
        self.assertIn('count>=0 && error==0', capture)  # partial timeout results rejected
        self.assertIn('tick_capture.Drain("timer",event_log)', ea)
        self.assertIn('tick_capture.Drain("deinit",event_log)', ea)
        self.assertNotIn('CopyRates', capture)
        log = (ROOT / "mt5/Include/TraderLab/EventLog.mqh").read_text(encoding="utf-8")
        self.assertIn('FileWriteString(handle,row); FileFlush(handle);', log)

    def test_native_cursor_checks_cover_history_boundary_and_multiplicity(self):
        checks = (ROOT / "mt5/StrategyChecks.mq5").read_text(encoding="utf-8")
        for assertion in ('one normal tick after startup', 'delayed callback drains three',
                          'overlap emits zero duplicate', 'same millisecond keeps distinct',
                          'whole ordered same-ms prefix', 'exact millisecond retained',
                          'historical ticks before capture startup', 'missing overlap fails closed',
                          'truncated boundary', 'reordered same-ms prefix',
                          'whole batch checked before any suffix', 'raw seconds and milliseconds must agree'):
            self.assertIn(assertion, checks)
        self.assertIn('TickCursorChecks();', checks)


if __name__ == "__main__":
    unittest.main()
