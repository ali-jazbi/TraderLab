"""Native source guards/comparator tests; NOT execution or proof of MQL parity."""
import copy
import json
from pathlib import Path
import unittest

from tools.compare_native_retests import compare_rows, EVENTS
from tools.inspect_capture import inspect_capture
from traderlab.replay import Engine
from test_tick_capture_evidence import loss_aware_capture
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def comparator_fixture():
    """Genuine quotes, delayed bar delivery + Python-shaped native diagnostics.

    This tests the comparison harness only; no native events are claimed real.
    """
    source = [json.loads(s) for s in (ROOT / 'tests/fixtures/oct07-retest-market.jsonl').read_text(
        encoding='utf-8').splitlines()]
    dispatch = {}; next_tick = None
    for i in range(len(source)-1, -1, -1):
        if source[i]['kind'] == 'tick':
            next_tick = source[i]
        dispatch[i] = next_tick
    config = json.loads((ROOT / 'configs/production.template.json').read_text(encoding='utf-8'))
    config["observation_price_side"]=None  # Native stream intentionally includes both diagnostic lanes.
    engine = Engine(config); rows = []
    for i, row in enumerate(source):
        tick = dispatch[i]
        if tick is None:
            continue
        if row['kind'] == 'bar':
            row = {**row, 'event': 'BOS_TRACKER_CLOSED_BAR', 'time': tick['time'],
                   'before_tick_index': tick['tick_index']}
        else:
            row = {**row, 'event': 'TICK'}
        rows.append(row); previous = len(engine.events); engine.accept(row)
        rows.extend({**e, 'millisecond_ordinal': row['millisecond_ordinal']}
                    for e in engine.events[previous:] if e['event'] in EVENTS)
    ticks = sum(r['event'] == 'TICK' for r in rows)
    rows.append({'event': 'BOS_TRACKER_SUMMARY', 'detection_halted': False, 'processed_ticks': ticks,
                 'automatic_setups': 0, 'intrabar_breaks': sum(r['event'] == EVENTS[0] for r in rows),
                 'first_returns': sum(r['event'] == EVENTS[1] for r in rows)})
    return rows, config


class NativeRetestChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.config = comparator_fixture()

    def test_comparator_matches_both_audited_candidates_without_claiming_full_parity(self):
        report = compare_rows(self.rows, self.config)
        self.assertTrue(report['matches'])
        self.assertGreaterEqual(report['native_events'], 6)
        self.assertEqual(report['full_native_python_parity'], 'NOT_ESTABLISHED')
        self.assertEqual(report['automatic_setups'], 0)

    def test_millisecond_disagreement_is_reported(self):
        rows = copy.deepcopy(self.rows)
        r = next(r for r in rows if r['event'] == EVENTS[1] and r['bos_id'].startswith('M1:BUY:2026-10-07T03:10'))
        r['first_return_at'] = '2026-10-07T03:25:58.052Z'
        self.assertFalse(compare_rows(rows, self.config)['matches'])

    def test_duplicates_halted_and_missing_native_stream_rejected(self):
        rows = copy.deepcopy(self.rows)
        r = next(r for r in rows if r['event'] == EVENTS[1])
        rows.insert(rows.index(r)+1, copy.deepcopy(r)); rows[-1]['first_returns'] += 1
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            compare_rows(rows, self.config)
        rows = copy.deepcopy(self.rows); rows[-1]['detection_halted'] = True
        with self.assertRaisesRegex(ValueError, 'halted'):
            compare_rows(rows, self.config)
        with self.assertRaisesRegex(ValueError, 'Fresh native'):
            compare_rows([], self.config)

    def test_asof_dispatch_time_and_tick_index_must_match(self):
        for field, value in (('before_tick_index', 999999), ('time', '2026-10-07T03:00:00Z')):
            rows = copy.deepcopy(self.rows)
            r = next(r for r in rows if r['event'] == 'BOS_TRACKER_CLOSED_BAR')
            r[field] = value
            with self.assertRaises(ValueError):
                compare_rows(rows, self.config)

    def test_diagnostic_must_follow_its_real_tick_occurrence(self):
        rows = copy.deepcopy(self.rows)
        r = next(r for r in rows if r['event'] == EVENTS[1])
        r['millisecond_ordinal'] += 1
        with self.assertRaisesRegex(ValueError, 'genuine dispatch tick'):
            compare_rows(rows, self.config)

    def test_native_observer_is_after_cursor_acceptance_and_not_callback_head(self):
        source = (ROOT / 'mt5/Include/TraderLab/TickCapture.mqh').read_text(encoding='utf-8')
        drain = source.split('void Drain(', 1)[1].split('void Summary(', 1)[0]
        self.assertLess(drain.index('TLConsumeHistory('), drain.index('observer.BeforeTick('))
        self.assertLess(drain.index('if(i<skip) continue;'), drain.index('observer.BeforeTick('))
        self.assertLess(drain.index('observer.BeforeTick('), drain.index('log.Write("TICK"'))
        self.assertLess(drain.index('log.Write("TICK"'), drain.index('observer.AfterTick('))
        self.assertIn('observer.AfterTick(tick,emitted,ordinal,log)', drain)
        self.assertNotIn('observer.AfterTick(head', drain)
        stream = (ROOT / 'mt5/Include/TraderLab/NativeRetestStream.mqh').read_text(encoding='utf-8')
        for frame in ('PERIOD_M1', 'PERIOD_M5', 'PERIOD_M15', 'PERIOD_H1', 'PERIOD_H4'):
            self.assertIn(frame, stream)
        self.assertIn('bars[i].time+seconds>tick.time', stream)
        self.assertIn('if(bucket==checked_bucket[tf]) continue;', stream)
        self.assertIn('trackers[i].ProcessTick(tick,index,ordinal,log)', stream)
        source = (ROOT / 'mt5/Include/TraderLab/Retests.mqh').read_text(encoding='utf-8')
        self.assertIn('ArrayResize(active,retained,256)', source)
        self.assertNotIn('ArrayResize(history,retained', source)

    def test_tracker_coarse_summary_does_not_weaken_tick_chronology(self):
        rows = loss_aware_capture()
        coarse = {**rows[-2], 'event': 'BOS_TRACKER_SUMMARY'}
        rows.insert(-2, coarse)
        for i, r in enumerate(rows, 1):
            r['seq'] = i
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'capture.jsonl'
            path.write_text('\n'.join(json.dumps(r) for r in rows)+'\n', encoding='utf-8')
            self.assertEqual(inspect_capture(path)['errors'], [])


if __name__ == '__main__':
    unittest.main()
