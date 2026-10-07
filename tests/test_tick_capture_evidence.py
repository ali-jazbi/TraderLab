"""Synthetic capture evidence tests; these do not execute MQL5 or a broker API."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_inspect_capture import event, valid_capture
from tools.inspect_capture import inspect_capture


NORMALIZER = Path(__file__).resolve().parents[1] / "tools/normalize_mt5_log.py"


def loss_aware_capture():
    base = valid_capture()
    msc = int(datetime(2026, 7, 1, 12, 0, 2, tzinfo=timezone.utc).timestamp()) * 1000 + 123
    start = event(3, "TICK_CAPTURE_START", base[1]["server_time"], base[1]["time"], base[1]["strategy_time"],
                  timestamp_precision="seconds", capture_version="loss_aware_v1", cursor_time_msc=msc - 1,
                  cursor_boundary_count=1, startup_policy="exclude_baseline_and_earlier_ticks",
                  same_millisecond_policy="ordered_full_prefix", timer_interval_ms=1000, broker_feed_complete=None)
    first = base[2]
    first.update(seq=4, timestamp_precision="milliseconds", time_msc=msc, broker_time_seconds=msc // 1000,
                 millisecond_ordinal=1, flags=6, last="0.0000000000000000", volume=0, volume_real="0.0")
    second = copy.deepcopy(first)
    second.update(seq=5, tick_index=2, millisecond_ordinal=2, flags=2)
    recovery = event(6, "TICK_CAPTURE_RECOVERY", first["server_time"], first["time"], first["strategy_time"],
                     timestamp_precision="milliseconds", source="ontick", first_tick_index=1,
                     last_tick_index=2, recovered_ticks=1)
    bar = base[3]
    bar.update(seq=7, time=first["time"], server_time=first["server_time"], strategy_time=first["strategy_time"],
               timestamp_precision="milliseconds")
    summary = event(8, "TICK_CAPTURE_SUMMARY", "2026-07-01T12:00:02.000", "2026-07-01T09:00:02.000Z",
                    "2026-07-01T12:30:02.000+03:30", timestamp_precision="seconds", capture_version="loss_aware_v1",
                    ontick_callbacks=1, drain_calls=3, copyticks_calls=4, emitted_ticks=2,
                    callback_snapshot_matches=1, recovered_ticks=1, duplicate_overlap_skips=6,
                    cursor_ambiguities=0, copyticks_errors=0, snapshot_errors=0, timer_errors=0,
                    terminal_cursor_evidence_valid=True, capture_halted=False, broker_feed_complete=None,
                    cursor_time_msc=msc, cursor_boundary_count=2)
    deinit = event(9, "EA_DEINIT", summary["server_time"], summary["time"], summary["strategy_time"],
                   timestamp_precision="seconds", reason=1)
    return [base[0], base[1], start, first, second, recovery, bar, summary, deinit]


class TickCaptureEvidenceChecks(unittest.TestCase):
    def inspect(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.jsonl"
            raw = "\n".join(json.dumps(row) for row in rows) + "\n"
            path.write_text(raw, encoding="utf-8")
            result = inspect_capture(path)
            self.assertEqual(path.read_text(encoding="utf-8"), raw)
            return result

    def test_same_millisecond_occurrences_and_summary_reconcile(self):
        result = self.inspect(loss_aware_capture())
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["tick_capture_summary"]["emitted_ticks"], 2)
        self.assertEqual([row["millisecond_ordinal"] for row in result["ticks"]], [1, 2])
        self.assertEqual([row["time"] for row in result["ticks"]], ["2026-07-01T09:00:02.123Z"] * 2)

    def test_v2_unmatched_callback_and_identical_history_ticks_reconcile(self):
        rows = loss_aware_capture()
        rows[2]["capture_version"] = rows[-2]["capture_version"] = "loss_aware_v2"
        rows[4]["flags"] = rows[3]["flags"]  # identical raw records retain two ordinals
        rows[5]["recovered_ticks"] = 2
        rows[-2].update(callback_snapshot_matches=0, recovered_ticks=2, copyticks_calls=5)
        result = self.inspect(rows)
        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["ticks"]), 2)
        self.assertEqual(result["tick_capture_summary"]["emitted_ticks"], 2)
        for changes in ({"recovered_ticks": 1}, {"copyticks_calls": 1},
                        {"copyticks_calls": 6}, {"capture_version": "loss_aware_v1"}):
            invalid = copy.deepcopy(rows)
            invalid[-2].update(changes)
            self.assertTrue(self.inspect(invalid)["errors"])

    def test_run04_snapshot_head_missing_remains_rejected(self):
        rows = loss_aware_capture()
        rows = rows[:3] + [rows[5], rows[-2], rows[-1]]
        rows[3].update(event="TICK_CAPTURE_AMBIGUITY", reason="snapshot_head_missing", source="ontick",
                       capture_halted=True)
        rows[4].update(ontick_callbacks=2988, drain_calls=3675, copyticks_calls=2,
                       emitted_ticks=0, callback_snapshot_matches=0, recovered_ticks=0,
                       duplicate_overlap_skips=0, cursor_ambiguities=1, capture_halted=True,
                       terminal_cursor_evidence_valid=False,
                       cursor_time_msc=rows[2]["cursor_time_msc"], cursor_boundary_count=1)
        for seq, row in enumerate(rows, 1):
            row["seq"] = seq
        result = self.inspect(rows)
        self.assertTrue(result["errors"])
        self.assertTrue(any("TICK_CAPTURE_AMBIGUITY" in error for error in result["errors"]))
        self.assertEqual(result["attention"][0]["event"], "TICK_CAPTURE_AMBIGUITY")
        self.assertEqual(result["rows"][3]["reason"], "snapshot_head_missing")

    def test_loss_aware_capture_requires_final_summary(self):
        rows = [row for row in loss_aware_capture() if row["event"] != "TICK_CAPTURE_SUMMARY"]
        self.assertTrue(any("final TICK_CAPTURE_SUMMARY" in error for error in self.inspect(rows)["errors"]))

    def test_errors_and_ambiguities_remain_prominent_even_after_retry(self):
        for name, counter in (("TICK_CAPTURE_ERROR", "copyticks_errors"), ("TICK_CAPTURE_AMBIGUITY", "cursor_ambiguities")):
            with self.subTest(name=name):
                rows = loss_aware_capture()
                rows[5].update(event=name, reason="boundary_prefix_changed")
                rows[-2][counter] = 1
                rows[-2]["terminal_cursor_evidence_valid"] = False
                result = self.inspect(rows)
                self.assertTrue(any(name in error for error in result["errors"]))
                self.assertEqual(result["attention"][0]["event"], name)

    def test_corrupted_raw_milliseconds_and_ordinals_fail(self):
        for field, value in (("time_msc", loss_aware_capture()[3]["time_msc"] + 1),
                             ("millisecond_ordinal", 1), ("broker_time_seconds", 0),
                             ("timestamp_precision", "seconds")):
            with self.subTest(field=field):
                rows = loss_aware_capture()
                rows[4][field] = value
                self.assertTrue(self.inspect(rows)["errors"])

    def test_before_startup_and_contiguous_indexes_cannot_fake_completeness(self):
        rows = loss_aware_capture()
        rows[2]["cursor_time_msc"] = rows[3]["time_msc"] + 1
        self.assertTrue(any("startup history" in error for error in self.inspect(rows)["errors"]))
        for field, value in (("broker_feed_complete", True), ("emitted_ticks", 3),
                             ("recovered_ticks", 2), ("cursor_boundary_count", 1), ("timer_errors", 1)):
            with self.subTest(field=field):
                rows = loss_aware_capture()
                rows[-2][field] = value
                self.assertTrue(self.inspect(rows)["errors"])

    def test_summary_must_follow_all_ticks(self):
        rows = loss_aware_capture()
        rows[-2], rows[4] = rows[4], rows[-2]
        self.assertTrue(any("summary is not final" in error for error in self.inspect(rows)["errors"]))

    def test_normalizer_preserves_two_same_ms_ticks_and_rejects_incomplete_evidence(self):
        for version, valid in (("loss_aware_v1", True), ("loss_aware_v2", True), ("loss_aware_v2", False)):
            with self.subTest(version=version, valid=valid), tempfile.TemporaryDirectory() as directory:
                capture, output = Path(directory) / "capture.jsonl", Path(directory) / "output.jsonl"
                rows = loss_aware_capture()
                rows[2]["capture_version"] = rows[-2]["capture_version"] = version
                if version == "loss_aware_v2":
                    rows[-2].update(callback_snapshot_matches=0, recovered_ticks=2, copyticks_calls=5)
                    rows[5]["recovered_ticks"] = 2
                if not valid:
                    rows.pop(-2)
                raw = "\n".join(json.dumps(row) for row in rows) + "\n"
                capture.write_text(raw, encoding="utf-8")
                result = subprocess.run([sys.executable, str(NORMALIZER), str(capture), str(output)],
                                        capture_output=True, text=True, check=False)
                self.assertEqual(capture.read_text(encoding="utf-8"), raw)
                if valid:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    ticks = [row for row in map(json.loads, output.read_text(encoding="utf-8").splitlines())
                             if row["kind"] == "tick"]
                    self.assertEqual(len(ticks), 2)
                    self.assertEqual([row["tick_index"] for row in ticks], [1, 2])
                    self.assertEqual([row["time"] for row in ticks], ["2026-07-01T09:00:02.123Z"] * 2)
                    self.assertEqual([row["flags"] for row in ticks], [6, 2])
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Loss-aware capture integrity failed", result.stderr)
                    self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
