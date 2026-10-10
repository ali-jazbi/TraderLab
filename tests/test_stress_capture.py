"""Synthetic evidence/CLI tests; do not execute MQL5 or the MT5 tester."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_tick_capture_evidence import loss_aware_capture
from tools.compare_stress_capture import compare_captures

ROOT = Path(__file__).resolve().parents[1]


def fixture(stress=False):
    rows = loss_aware_capture()
    rows[2]["capture_version"] = rows[-2]["capture_version"] = "loss_aware_v2"
    rows[-2]["ontick_callbacks"] = 4
    # Legitimate identical raw occurrences retain distinct ordinals.
    rows[4]["flags"] = rows[3]["flags"]
    if stress:
        rows[-2].update(callback_snapshot_matches=0, recovered_ticks=2)
        rows[5]["recovered_ticks"] = 2
    config = copy.deepcopy(rows[2])
    config.update(event="TESTER_STRESS_CONFIG", environment="strategy_tester", enabled=stress,
                  skip_callbacks=2, policy="skip_n_drain_one_after_baseline", timer_policy="hold_during_skips")
    summary = copy.deepcopy(rows[-2])
    summary.update(event="TESTER_STRESS_SUMMARY", environment="strategy_tester", enabled=stress,
                   callbacks_seen=4, skipped_callbacks=2 if stress else 0,
                   deferred_timer_calls=1 if stress else 0)
    rows.insert(2, config)
    rows.insert(-2, summary)
    for seq, row in enumerate(rows, 1):
        row["seq"] = seq
    return rows


class StressCaptureChecks(unittest.TestCase):
    def compare(self, normal, stress, cli=False):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / "normal.jsonl", Path(directory) / "stress.jsonl"]
            raw = ["\n".join(json.dumps(r) for r in rows) + "\n" for rows in (normal, stress)]
            for path, content in zip(paths, raw):
                path.write_text(content, encoding="utf-8")
            if cli:
                run = subprocess.run([sys.executable, str(ROOT / "tools/compare_stress_capture.py"), *map(str, paths)],
                                     capture_output=True, text=True, check=False)
                result = json.loads(run.stdout)
                self.assertEqual(run.returncode, 0 if result["status"] == "PASS" else 1, run.stderr)
            else:
                result = compare_captures(*paths)
            for path, content in zip(paths, raw):
                self.assertEqual(path.read_text(encoding="utf-8"), content)
            return result

    def test_exact_sequence_cli_preserves_identical_same_ms_occurrences(self):
        result = self.compare(fixture(), fixture(True), cli=True)
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["emitted_ticks"], 2)
        self.assertEqual(result["duplicate_occurrences"], 0)
        self.assertEqual(result["stress_recovered_ticks"], 2)
        self.assertEqual(result["skipped_callbacks"], 2)
        self.assertEqual(len(result["tick_sequence_sha256"]), 64)

    def test_raw_field_or_occurrence_mutation_fails(self):
        for field, value in (("flags", 2), ("volume", 10), ("last", "4147.0"),
                             ("volume_real", "1.0"), ("millisecond_ordinal", 1),
                             ("time", "2026-07-01T09:00:02.124Z"),
                             ("time_msc", next(r for r in fixture(True) if r.get("kind") == "tick")["time_msc"] + 1)):
            with self.subTest(field=field):
                stress = fixture(True)
                next(r for r in reversed(stress) if r.get("kind") == "tick")[field] = value
                self.assertEqual(self.compare(fixture(), stress)["status"], "FAIL")

    def test_different_baselines_are_not_trimmed(self):
        stress = fixture(True)
        next(r for r in stress if r["event"] == "TICK_CAPTURE_START")["cursor_time_msc"] -= 1
        result = self.compare(fixture(), stress)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("baselines differ", result["errors"][0])

    def test_valid_but_shorter_stress_sequence_fails(self):
        stress = fixture(True)
        stress.remove(next(r for r in stress if r.get("tick_index") == 2))
        next(r for r in stress if r["event"] == "TICK_CAPTURE_RECOVERY").update(last_tick_index=1, recovered_ticks=1)
        next(r for r in stress if r["event"] == "TICK_CAPTURE_SUMMARY").update(emitted_ticks=1, recovered_ticks=1, cursor_boundary_count=1)
        for seq, row in enumerate(stress, 1):
            row["seq"] = seq
        result = self.compare(fixture(), stress, cli=True)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("counts differ" in error for error in result["errors"]), result)

    def test_zero_recovery_or_wrong_schedule_fails(self):
        stress = fixture(True)
        stress = [r for r in stress if r["event"] != "TICK_CAPTURE_RECOVERY"]
        next(r for r in stress if r["event"] == "TICK_CAPTURE_SUMMARY").update(recovered_ticks=0, callback_snapshot_matches=2)
        for seq, row in enumerate(stress, 1):
            row["seq"] = seq
        result = self.compare(fixture(), stress)
        self.assertTrue(any("recovered_ticks must" in error for error in result["errors"]), result)
        for field, value in (("skipped_callbacks", 0), ("callbacks_seen", 5), ("enabled", False)):
            stress = fixture(True)
            next(r for r in stress if r["event"] == "TESTER_STRESS_SUMMARY")[field] = value
            self.assertEqual(self.compare(fixture(), stress)["status"], "FAIL")

    def test_capture_errors_and_incomplete_metadata_are_rejected(self):
        for counter in ("cursor_ambiguities", "copyticks_errors", "snapshot_errors", "timer_errors"):
            stress = fixture(True)
            next(r for r in stress if r["event"] == "TICK_CAPTURE_SUMMARY")[counter] = 1
            self.assertEqual(self.compare(fixture(), stress)["status"], "FAIL")
        stress = [r for r in fixture(True) if r["event"] != "TESTER_STRESS_CONFIG"]
        self.assertEqual(self.compare(fixture(), stress)["status"], "FAIL")

    def test_native_stress_is_tester_gated_and_final_drain_is_unconditional(self):
        ea = (ROOT / "mt5/TraderLab.mq5").read_text(encoding="utf-8")
        tester = ea.split('if(MQLInfoInteger(MQL_TESTER))', 1)[1].split('   if(!tick_capture.Start(', 1)[0]
        self.assertIn('tester_stress.Configure(true,InpTesterStress,InpTesterStressSkipCallbacks)', tester)
        self.assertEqual(ea.count('tester_stress.Configure('), 1)
        self.assertIn('input bool InpTesterStress=false;', ea)
        self.assertIn('tick_capture.OnCallback(event_log,!skip)', ea)
        self.assertIn('tester_stress.SkipTimer()', ea)
        deinit = ea.split('void OnDeinit(', 1)[1]
        self.assertIn('tick_capture.Drain("deinit",event_log)', deinit)
        self.assertNotIn('SkipTimer()', deinit)
        self.assertLess(deinit.index('TESTER_STRESS_SUMMARY'), deinit.index('tick_capture.Summary('))
        capture = (ROOT / "mt5/Include/TraderLab/TickCapture.mqh").read_text(encoding="utf-8")
        self.assertIn('callbacks++; if(drain) Drain("ontick",log)', capture)
        scheduler = (ROOT / "mt5/Include/TraderLab/TesterStress.mqh").read_text(encoding="utf-8")
        self.assertIn('enabled=tester && requested;', scheduler)
        self.assertIn('if(!enabled || callbacks==1)', scheduler)
        for forbidden in ('MqlTick', 'CopyTicks', 'SymbolInfoTick', 'Sleep('):
            self.assertNotIn(forbidden, scheduler)
        checks = (ROOT / "mt5/StrategyChecks.mq5").read_text(encoding="utf-8")
        self.assertIn('TesterStressChecks();', checks)
        self.assertIn('stress raw tick sequence exactly equals normal', checks)


if __name__ == "__main__":
    unittest.main()
