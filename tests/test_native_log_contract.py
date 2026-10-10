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

    def test_history_acceptance_is_independent_of_quote_snapshot(self):
        source = (ROOT / "mt5/Include/TraderLab/TickCapture.mqh").read_text(encoding="utf-8")
        start = source.split('bool Start(const string', 1)[1].split('void OnCallback', 1)[0]
        drain = source.split('void Drain(', 1)[1].split('void Summary(', 1)[0]
        helper = source.split('bool TLConsumeHistory(', 1)[1].split('class TLTickCapture', 1)[0]
        self.assertIn('CopyTicks(symbol,recent,COPY_TICKS_ALL,0,1)', source)
        self.assertIn('ReadRange(seed.time_msc,0,baseline', start)
        self.assertNotIn('ReadHead', start)
        self.assertIn('ReadRange(cursor.Millisecond(),0,ticks', drain)
        self.assertNotIn('head.time_msc', drain)
        self.assertNotIn('ContainsHead', source)
        self.assertNotIn('snapshot_head_missing', source)
        self.assertLess(helper.index('cursor.Consume('), helper.index('if(match_snapshot)'))
        self.assertNotIn('return false', helper.split('if(match_snapshot)', 1)[1])
        checks = (ROOT / "mt5/StrategyChecks.mq5").read_text(encoding="utf-8")
        for assertion in ('run04 same time_msc differing raw', 'history lagging current quote snapshot',
                          'unmatched callback counters reconcile', 'older quote snapshot never limits',
                          'history boundary mutation still fails closed',
                          'history boundary reordering still fails closed',
                          'startup history snapshot excludes all earlier milliseconds'):
            self.assertIn(assertion, checks)
        self.assertIn('HistoryAuthorityChecks();', checks)

    def test_tester_defers_history_and_timer_until_first_ontick_only(self):
        source = (ROOT / "mt5/TraderLab.mq5").read_text(encoding="utf-8")
        init = source.split('int OnInit()', 1)[1].split('void OnTick()', 1)[0]
        tester = init.split('if(MQLInfoInteger(MQL_TESTER))', 1)[1].split('   if(!tick_capture.Start(', 1)[0]
        self.assertIn('tester_start_pending=true;', tester)
        self.assertIn('TICK_CAPTURE_START_DEFERRED', tester)
        self.assertIn('first_callback_history_is_baseline', tester)
        self.assertIn('return INIT_SUCCEEDED;', tester)
        self.assertNotIn('tick_capture.Start(', tester)
        self.assertNotIn('StartTimer(', tester)
        self.assertNotIn('CopyTicks', tester)
        live = init.split(tester, 1)[1]
        self.assertIn('if(!tick_capture.Start(InpBrokerSymbol,event_log)) return INIT_FAILED;', live)
        self.assertIn('if(!tick_capture.StartTimer(event_log)) return INIT_FAILED;', live)
        tick = source.split('void OnTick()', 1)[1].split('void ProcessClosedBars()', 1)[0]
        self.assertLess(tick.index('tester_start_pending=false;'), tick.index('tick_capture.Start('))
        self.assertIn('ExpertRemove();', tick)
        self.assertIn('return;', tick.split('ExpertRemove();', 1)[1])
        timer = source.split('void OnTimer()', 1)[1].split('void OnDeinit', 1)[0]
        self.assertLess(timer.index('if(tester_start_pending) return;'), timer.index('tick_capture.Drain('))
        self.assertIn('tester_no_first_tick', source)
        self.assertNotIn('Sleep(', source)
        checks = (ROOT / "mt5/StrategyChecks.mq5").read_text(encoding="utf-8")
        self.assertIn('TesterBaselineChecks();', checks)
        self.assertIn('tester later same-ms occurrence emitted', checks)


if __name__ == "__main__":
    unittest.main()
