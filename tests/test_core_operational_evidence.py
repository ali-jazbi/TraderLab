"""Calendar/measurement checks; native reducer scenarios are separately executed in MT5."""
from datetime import date, timezone
import json
from pathlib import Path
import tempfile
import unittest
from tools.build_core_calendar import build, utc
from tools.measure_demo_evidence import broker_results, spread_sample

ROOT = Path(__file__).resolve().parents[1]


class OperationalEvidenceChecks(unittest.TestCase):
    def source(self):
        return json.loads((ROOT / "configs/core-calendar.sources-20261013.json").read_text(encoding="utf-8"))

    def test_sourced_one_day_and_cpi_exact_utc_no_invented_events(self):
        text, manifest = build(self.source(), "2026-10-14")
        self.assertEqual(manifest["session_start_utc"], "2026-10-13T20:00:00+00:00")
        self.assertEqual(manifest["session_end_utc"], "2026-10-14T21:00:00+00:00")
        self.assertEqual(len([x for x in text.splitlines() if x.startswith("DAY|")]), 1)
        self.assertEqual(manifest["events_in_coverage"][0]["utc"], "2026-10-14T12:30:00+00:00")
        self.assertEqual(manifest["events_in_coverage"][0]["name"], "CPI")
        self.assertIsNone(manifest["adjacent_day_overlap_policy"])
        self.assertFalse(manifest["broker_execution_enabled"])

    def test_independent_sydney_and_new_york_dst_conversions(self):
        self.assertEqual(utc(date(2026, 10, 2), "07:00", "Australia/Sydney").hour, 21)
        self.assertEqual(utc(date(2026, 10, 5), "07:00", "Australia/Sydney").hour, 20)
        self.assertEqual(utc(date(2026, 10, 30), "17:00", "America/New_York").hour, 21)
        self.assertEqual(utc(date(2026, 11, 2), "17:00", "America/New_York").hour, 22)

    def test_days_do_overlap_so_the_builder_never_silently_allocates_reset(self):
        _, first = build(self.source(), "2026-10-13")
        _, second = build(self.source(), "2026-10-14")
        self.assertGreater(first["session_end_utc"], second["session_start_utc"])
        for day in ("2026-10-17", "2026-11-02"):
            with self.assertRaises(ValueError):
                build(self.source(), day)
        invalid = self.source()
        invalid["news_coverage_end"] = "2026-10-13T10:00:00Z"
        with self.assertRaises(ValueError):
            build(invalid, "2026-10-13")

    def test_spread_is_real_quote_measurement_not_recommended_cap(self):
        rows = [{"seq": i+1, "event": "TICK", "symbol": "XAUUSD_o", "tick_index": i+1,
                 "time_msc": 1791331200000+i, "time": f"2026-10-07T00:00:00.00{i}Z",
                 "server_time": f"2026-10-07T00:00:00.00{i}", "server_utc_offset_seconds": 0,
                 "bid": "4140.00", "ask": ask} for i, ask in enumerate(("4140.22", "4140.22", "4140.52"))]
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "fixture.jsonl"
            p.write_text("".join(json.dumps(r)+"\n" for r in rows) + '{"unfinished":', encoding="utf-8")
            report = spread_sample(p, True)
            self.assertEqual(report["ticks"], 3)
            self.assertEqual(report["spread_price"]["p50"], "0.22")
            self.assertEqual(report["spread_price"]["max"], "0.52")
            self.assertGreater(report["unread_incomplete_suffix_bytes"], 0)
            with self.assertRaises(ValueError):
                spread_sample(p)
            rows[1]["tick_index"] = 3
            p.write_text("".join(json.dumps(r)+"\n" for r in rows), encoding="utf-8")
            with self.assertRaises(ValueError):
                spread_sample(p, True)

    def test_actual_fill_requires_a_matching_broker_deal_and_does_not_set_limits(self):
        journal = ("market buy 0.01 XAUUSD_o\n"
                   "deal #1 buy 0.01 XAUUSD_o at 4142.54 done\n"
                   "order #10 buy 0.01 / 0.01 XAUUSD_o at 4142.54 done in 100.884 ms\n"
                   "market sell 0.01 XAUUSD_o, close #10 buy 0.01 XAUUSD_o\n"
                   "order #11 sell 0.01 / 0.01 XAUUSD_o at 4142.20 done in 98.422 ms")
        experts = ("TL_DEMO_AUTO_CHECK: side=BUY lot=0.01 bid=4142.32 ask=4142.54\n"
                   "TL_DEMO_AUTO_ENTRY: attempt=1 sent=1 retcode=10009 deal=1 order=10 price=4142.54")
        report = broker_results(journal, experts)
        self.assertEqual(report["matched_entry_fill_slippage_price"], ["0.00"])
        self.assertEqual(report["orders"]["close"]["max_ms"], "98.422")
        self.assertFalse(report["limits_approved"])
        with self.assertRaises(ValueError):
            broker_results(journal.replace("deal #1 ", "deal #2 "), experts)

    def test_native_core_uses_tested_trade_reducers_and_durable_day_boundary(self):
        s = (ROOT / "mt5/Include/TraderLab/CoreLifecycle.mqh").read_text(encoding="utf-8")
        observer = s[s.index("bool ObserveDeal"):]
        self.assertIn("TLCoreTradeFill(trades[i]", observer)
        self.assertIn("TLCoreTradeExit(trades[i]", observer)
        self.assertIn("TLCorePairedEvidence(trades[n])", s)
        self.assertIn('FileWrite(plan_file,"DAY"', s)
        self.assertIn('if(kind=="DAY")', s)
        self.assertIn("CORE_DAY_OVERLAP_OR_MUTATION_UNRESOLVED", s)
        checks = (ROOT / "mt5/CorePipelineChecks.mq5").read_text(encoding="utf-8")
        self.assertIn("LifecycleScenarios();", checks)
        self.assertIn("restart reconstructs pending BE from broker history", checks)
        self.assertIn("authoritative emergency exits close both", checks)


if __name__ == "__main__":
    unittest.main()
