import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest

from traderlab.detection import Bar, Detector, big_candle, fvg
from traderlab.replay import Engine, run
from traderlab.session import NYBias, news_block
from traderlab.strategy import Bos, DailyGuard, Unresolved, Zone, breakeven, core_plan, number, ob_broken, select_bos

ROOT = Path(__file__).resolve().parents[1]
D = Decimal


def config():
    return json.loads((ROOT / "configs/fixture.example.json").read_text())


def bos(price, name=None):
    p = D(price)
    return Bos(name or price, p, Zone(p, p))


def setup_event(setup_id="S", side="BUY", entries=("4146", "4143"), stamp="2026-10-05T07:00:00Z"):
    return {"kind": "setup", "time": stamp, "setup_id": setup_id, "side": side,
            "source": "synthetic-test-annotation", "confirmed": True, "fill_state": "UNFILLED",
            "fvg": ["4140", "4148"], "ob": ["4135", "4137"],
            "bos": [{"id": f"{setup_id}-{i}", "entry": p, "zone": [p, p]} for i, p in enumerate(entries)]}


def tick(price, second, ask=None):
    return {"kind": "tick", "time": f"2026-10-05T07:00:{second:02d}Z", "bid": price, "ask": ask or price}


def bar_event(index, o="4143", h="4145", low="4143", c="4144", timeframe="M1", start=None):
    start = start or datetime(2026, 10, 5, tzinfo=timezone.utc)
    seconds = {"M1": 60, "M5": 300, "M15": 900, "H1": 3600, "H4": 14400}[timeframe]
    opened = start + timedelta(seconds=index * seconds)
    return {"kind": "bar", "time": (opened + timedelta(seconds=seconds)).isoformat(),
            "opened_at": opened.isoformat(), "timeframe": timeframe, "open": o, "high": h, "low": low, "close": c}


class CanonicalRules(unittest.TestCase):
    def test_dual_buy_and_sell_levels(self):
        p = core_plan("BUY", [bos("4146"), bos("4143")], {})
        self.assertEqual((p.stop, p.target1, p.target2), (D("4140"), D("4152"), D("4156")))
        sell = core_plan("SELL", [bos("4146"), bos("4143")], {})
        self.assertEqual((sell.stop, sell.target1, sell.target2), (D("4149"), D("4137"), D("4133")))

    def test_distance_boundaries(self):
        for high, low, count in (("4146", "4145", 1), ("4146", "4144", 1),
                                 ("4146", "4143.99", 2), ("4146", "4142", 2)):
            for side, expected in (("BUY", high), ("SELL", low)):
                selected = select_bos(side, [bos(high), bos(low)])
                self.assertEqual(len(selected), count)
                self.assertEqual(selected[0].entry, D(expected))
        for low in ("4145.01", "4141.99"):
            with self.assertRaises(Unresolved):
                select_bos("BUY", [bos("4146"), bos(low)])

    def test_extremes_and_single_sl_unresolved(self):
        selected = select_bos("BUY", [bos("4146"), bos("4145"), bos("4144"), bos("4143")])
        self.assertEqual([b.entry for b in selected], [D("4146"), D("4143")])
        with self.assertRaises(Unresolved):
            core_plan("BUY", [bos("4146"), bos("4144")], {})

    def test_be_and_ob_threshold(self):
        p = core_plan("BUY", [bos("4146"), bos("4143")], {})
        with self.assertRaises(Unresolved):
            breakeven(p, D("4143"), {})
        self.assertEqual(breakeven(p, D("4143"), {"multi_entry_be_reference": "own_entry"}), D("4143.5"))
        self.assertEqual(breakeven(p, D("4143"), {"multi_entry_be_reference": "shared_reference"}), D("4146.5"))
        self.assertTrue(ob_broken("BUY", Zone(D("4141"), D("4143")), D("4140")))
        self.assertFalse(ob_broken("BUY", Zone(D("4141"), D("4143")), D("4140.01")))
        self.assertTrue(ob_broken("SELL", Zone(D("4141"), D("4143")), D("4144")))

    def test_daily_stops_grouped_and_profit_latched(self):
        day = DailyGuard()
        day.reset("A")
        day.close("first", D("-12"), True)
        day.close("first", D("-6"), True)
        self.assertEqual(len(day.stopped_setups), 1)
        self.assertFalse(day.halted)
        day.close("second", D("3"), False)  # mixed stop/target still counted once
        day.close("second", D("-2"), True)
        self.assertTrue(day.halted)
        day.reset("B")
        day.close("winner", D("100"), False)
        day.close("another", D("20"), False)
        self.assertTrue(day.profit_reached)
        self.assertFalse(day.halted)
        day.close("loss", D("-2"), True)
        self.assertTrue(day.halted)

    def test_decimal_validation(self):
        for value in (float("nan"), "NaN", "Infinity", True, 0.1):
            with self.assertRaises(ValueError):
                number(value)


class DetectionChecks(unittest.TestCase):
    def window(self):
        result = []
        for i in range(21):
            args = ("4140", "4141", "4139", "4141") if i < 10 else ("4143", "4145", "4143", "4144")
            if i == 10:
                args = ("4140", "4147", "4140", "4146")
            result.append(Bar.read(bar_event(i, *args)))
        return result

    def test_ten_future_bars_and_geometry(self):
        detector = Detector()
        window = self.window()
        seen = []
        for bar in window[:20]:
            seen.extend(detector.accept(bar))
        self.assertFalse(any(e["event"] == "BIG_CANDLE_CONFIRMED" for e in seen))
        result = detector.accept(window[20])
        big = next(e for e in result if e["event"] == "BIG_CANDLE_CONFIRMED")
        self.assertEqual(big["candidate_at"], window[10].opened)
        self.assertEqual(big["available_at"], window[20].available)
        gap = next(e for e in result if e["event"] == "FVG_CONFIRMED")
        self.assertEqual(gap["zone"], [D("4141"), D("4143")])
        self.assertEqual(gap["fill_state"], "UNFILLED")
        self.assertFalse(gap["tradable_setup"])

    def test_filled_before_delayed_confirmation(self):
        window = self.window()
        window[15] = Bar.read(bar_event(15, "4141", "4143", "4140", "4142"))
        result = []
        detector = Detector()
        for bar in window:
            result = detector.accept(bar)
        self.assertEqual(next(e for e in result if e["event"] == "FVG_CONFIRMED")["fill_state"], "FULL")

    def test_body_threshold_inclusive(self):
        bars = [Bar.read(bar_event(i, "10", "30", "5", "11")) for i in range(21)]
        bars[10] = Bar.read(bar_event(10, "10", "30", "5", "12"))
        self.assertTrue(big_candle(bars))
        bars[10] = Bar.read(bar_event(10, "10", "30", "5", "11.99"))
        self.assertFalse(big_candle(bars))

    def test_bos_qualification_must_precede_break(self):
        detector = Detector()
        detector.accept(Bar.read(bar_event(0, "95", "100", "90", "96")))
        qualifies = detector.accept(Bar.read(bar_event(1, "92", "99", "88", "89")))
        self.assertTrue(any(e["event"] == "BOS_CANDIDATE_QUALIFIED" and e["side"] == "BUY" for e in qualifies))
        breaks = detector.accept(Bar.read(bar_event(2, "96", "101", "95", "100")))
        matching = next(e for e in breaks if e["side"] == "BUY" and e["candidate_at"] == datetime(2026, 10, 5, tzinfo=timezone.utc))
        self.assertTrue(matching["qualified_before_break"])
        second = Detector()
        second.accept(Bar.read(bar_event(0, "95", "100", "90", "96")))
        ambiguous = second.accept(Bar.read(bar_event(1, "92", "101", "88", "89")))
        e = next(e for e in ambiguous if e["side"] == "BUY")
        self.assertFalse(e["qualified_before_break"])
        self.assertTrue(e["same_bar_order_ambiguous"])

    def test_no_open_or_duplicate_bar(self):
        event = bar_event(0)
        event["time"] = event["opened_at"]
        with self.assertRaises(ValueError):
            Bar.read(event)
        detector = Detector()
        b = Bar.read(bar_event(0))
        detector.accept(b)
        with self.assertRaises(ValueError):
            detector.accept(b)


class ReplayChecks(unittest.TestCase):
    def test_full_tp_38_and_first_touch(self):
        engine = Engine(config())
        for line in (ROOT / "tests/canonical-buy.jsonl").read_text().splitlines():
            engine.accept(json.loads(line))
        self.assertEqual(engine.daily.closed_profit, D("38"))
        self.assertEqual(sum(e["event"] == "PAPER_ENTRY" for e in engine.events), 2)
        engine.accept(tick("4146", 5))
        self.assertEqual(sum(e["event"] == "PAPER_ENTRY" for e in engine.events), 2)
        self.assertEqual(sum(e["event"] == "BE_MOVED" for e in engine.events), 2)

    def test_full_sl_18_counts_once_no_auto_reverse(self):
        engine = Engine(config())
        for event in (setup_event(), tick("4146", 1), tick("4143", 2), tick("4140", 3)):
            engine.accept(event)
        self.assertEqual(engine.daily.closed_profit, D("-18"))
        self.assertEqual(len(engine.daily.stopped_setups), 1)
        self.assertFalse(any(e["event"] == "REVERSE_ARMED" for e in engine.events))

    def test_partial_policy_missing_consumes_touch(self):
        cfg = config()
        cfg["partial_fill_policy"] = None
        engine = Engine(cfg)
        engine.accept(setup_event())
        engine.accept(tick("4146", 1))
        engine.config["partial_fill_policy"] = "allow_any_partial"
        engine.accept(tick("4146", 2))
        self.assertEqual(len(engine.positions), 0)
        self.assertIn("S-0", engine.consumed_bos)

    def test_missing_config_never_silently_trades(self):
        for key in ("daily_reset_zone", "daily_reset_minute", "news_calendar", "contract_size",
                    "commission_usd_per_lot_per_side", "slippage_pips", "multi_entry_be_reference", "daily_profit_basis"):
            cfg = config()
            cfg[key] = None
            engine = Engine(cfg)
            engine.accept(setup_event())
            engine.accept(tick("4146", 1))
            self.assertFalse(engine.positions, key)
            self.assertTrue(any(e["event"] == "ENTRY_BLOCKED" for e in engine.events), key)

    def test_news_bounds_and_no_coverage(self):
        cfg = config()
        cfg["news_calendar"]["events"] = [{"name": "CPI", "available_at": "2026-10-05T00:00:00Z", "scheduled_at": "2026-10-05T07:30:00Z"}]
        for minute in (15, 30, 45):
            self.assertTrue(news_block(cfg, datetime(2026, 10, 5, 7, minute, tzinfo=timezone.utc), False))
        self.assertFalse(news_block(cfg, datetime(2026, 10, 5, 7, 14, 59, tzinfo=timezone.utc), False))
        with self.assertRaises(Unresolved):
            news_block(cfg, datetime(2026, 10, 7, tzinfo=timezone.utc), False)
        cfg["news_reverse_policy"] = None
        with self.assertRaises(Unresolved):
            news_block(cfg, datetime(2026, 10, 5, 7, 30, tzinfo=timezone.utc), True)

    def test_news_first_touch_not_retried(self):
        cfg = config()
        cfg["news_calendar"]["events"] = [{"name": "NFP", "available_at": "2026-10-05T00:00:00Z", "scheduled_at": "2026-10-05T07:00:00Z"}]
        engine = Engine(cfg)
        engine.accept(setup_event())
        engine.accept(tick("4146", 1))
        e = tick("4146", 2)
        e["time"] = "2026-10-05T08:00:00Z"
        engine.accept(e)
        self.assertFalse(engine.positions)

    def test_canonical_reverse_waits_for_original_entry(self):
        engine = Engine(config())
        event = setup_event(entries=("4146.5",))
        event["ob"], event["fvg"] = ["4141", "4143"], ["4143", "4147"]
        engine.accept(event)
        engine.accept(tick("4146.5", 1))
        engine.accept(tick("4140", 2))
        engine.accept({"kind": "structure", "time": "2026-10-05T07:00:03Z", "setup_id": "S",
                       "source": "canonical-C synthetic confirmed iFVG", "bos_broken": True, "ifvg_confirmed": True})
        self.assertTrue(engine.setups["S"].reverse_armed)
        self.assertEqual(sum(p.reverse for p in engine.positions), 0)
        engine.accept(tick("4142", 4))
        self.assertEqual(sum(p.reverse for p in engine.positions), 0)
        engine.accept(tick("4146.5", 5))
        reverse = [p for p in engine.positions if p.reverse]
        self.assertEqual(len(reverse), 2)
        self.assertEqual(reverse[0].entry, D("4146.5"))
        self.assertEqual([p.target for p in reverse], [D("4140.5"), D("4136.5")])

    def test_reverse_uses_planned_core_entry_not_actual_slipped_fill(self):
        cfg = config()
        cfg["slippage_pips"] = "2"
        engine = Engine(cfg)
        event = setup_event(entries=("4146.5",))
        event["ob"], event["fvg"] = ["4141", "4143"], ["4143", "4147"]
        engine.accept(event)
        engine.accept(tick("4146.3", 1, "4146.5"))
        setup = engine.setups["S"]
        self.assertEqual(setup.planned_core_entry["S-0"], D("4146.5"))
        self.assertEqual(setup.actual_core_fill["S-0"], D("4146.7"))
        self.assertEqual(engine.positions[0].entry, D("4146.7"))
        engine.accept(tick("4140.2", 2, "4140.4"))  # Stopped at first executable quote, plus configured slip.
        engine.accept(tick("4140", 3, "4140.2"))    # Wick confirms the 10-pip OB penetration.
        engine.accept({"kind": "structure", "time": "2026-10-05T07:00:04Z", "setup_id": "S",
                       "source": "explicit synthetic confirmed BOS+iFVG", "bos_broken": True,
                       "ifvg_confirmed": True})
        self.assertTrue(setup.reverse_armed)

        engine.accept(tick("4146.7", 5, "4146.9"))
        self.assertFalse(any(position.reverse for position in engine.positions))
        self.assertEqual([e["event"] for e in engine.events if e["event"] == "PAPER_ENTRY"], ["PAPER_ENTRY"])

        engine.accept(tick("4146.5", 6, "4146.7"))
        reverse = [position for position in engine.positions if position.reverse]
        self.assertEqual(len(reverse), 2)
        self.assertTrue(all(position.plan.entries[0].entry == D("4146.5") for position in reverse))
        self.assertTrue(all(position.entry == D("4146.3") for position in reverse))
        reverse_event = [e for e in engine.events if e["event"] == "PAPER_ENTRY" and e["reverse"]][0]
        self.assertEqual(reverse_event["planned_core_entry"], "4146.5")
        self.assertEqual(reverse_event["actual_core_fill"], "4146.7")

    def test_stop_gap_uses_first_observed_quote_and_tp_fill_is_explicit(self):
        cfg = config()
        cfg["slippage_pips"] = "0"
        engine = Engine(cfg)
        engine.accept(setup_event(entries=("4146",)))
        engine.accept(tick("4146", 1))
        engine.accept(tick("4140", 2, "4140.2"))
        stop = next(e for e in engine.events if e["event"] == "PAPER_EXIT" and e["exit_reason"] == "SL")
        self.assertEqual(D(stop["price"]), D("4140"))
        self.assertNotEqual(stop["price"], "4142")

        for fill_policy, expected in (("target", "4152"), ("quote", "4154")):
            tp_config = config()
            tp_config["tp_fill_policy"] = fill_policy
            tp_config["slippage_pips"] = "0"
            take_profit = Engine(tp_config)
            take_profit.accept(setup_event(entries=("4146",)))
            take_profit.accept(tick("4146", 1))
            take_profit.accept(tick("4154", 2, "4154.2"))
            exit_row = next(e for e in take_profit.events if e["event"] == "PAPER_EXIT")
            self.assertEqual(D(exit_row["price"]), D(expected), fill_policy)
            self.assertEqual(exit_row["exit_reason"], "TP1")

    def test_reverse_requires_every_condition_and_sl(self):
        cfg = config()
        cfg["breaker_sl_pips"] = None
        engine = Engine(cfg)
        event = setup_event(entries=("4146.5",))
        event["ob"], event["fvg"] = ["4141", "4143"], ["4143", "4147"]
        engine.accept(event)
        engine.accept(tick("4146.5", 1))
        engine.accept(tick("4140.1", 2))
        engine.accept({"kind": "structure", "time": "2026-10-05T07:00:03Z", "setup_id": "S",
                       "source": "test", "bos_broken": True, "ifvg_confirmed": True})
        self.assertFalse(engine.setups["S"].reverse_armed)  # OB lacks full10-pip penetration.
        engine.accept(tick("4140", 4))
        self.assertFalse(engine.setups["S"].reverse_armed)  # General SL still unknown.
        self.assertTrue(any(e.get("context") == "reverse" and "breaker_sl_pips" in e.get("reason", "") for e in engine.events))

    def test_invalid_time_duplicate_zone_and_gap(self):
        engine = Engine(config())
        engine.accept(setup_event())
        other = setup_event("other")
        other["bos"][0]["id"] = "S-0"
        with self.assertRaises(ValueError):
            engine.accept(other)
        with self.assertRaises(ValueError):
            engine.accept(tick("4146", 1, "4145"))
        engine.accept(tick("4148", 2))
        engine.accept(tick("4144", 3))
        self.assertIn("S-0", engine.consumed_bos)
        self.assertFalse(engine.positions)
        with self.assertRaises(ValueError):
            engine.accept(tick("4146", 1))

    def test_equal_time_ticks_require_capture_sequence(self):
        engine = Engine(config())
        first = tick("4148", 1)
        first["tick_index"] = 1
        second = tick("4147", 1)
        second["tick_index"] = 2
        engine.accept(first)
        engine.accept(second)
        with self.assertRaises(ValueError):
            engine.accept(second)

    def test_full_fill_blocks_core_and_no_temporary_config_fallback(self):
        engine = Engine(config())
        event = setup_event()
        event["fill_state"] = "FULL"
        engine.accept(event)
        engine.accept(tick("4146", 1))
        self.assertFalse(engine.positions)
        self.assertTrue(any(e.get("reason") == "FVG_FULL_FILL_INVALID" for e in engine.events))

    def test_costs_and_quote_spread_are_explicit(self):
        cfg = config()
        cfg["commission_usd_per_lot_per_side"] = "10"
        cfg["slippage_pips"] = "1"
        engine = Engine(cfg)
        engine.accept(setup_event())
        engine.accept(tick("4145.8", 1, "4146"))
        self.assertEqual(engine.positions[0].entry, D("4146.1"))
        engine.accept(tick("4139.8", 2, "4140"))
        self.assertEqual(engine.daily.closed_profit, D("-13.200"))

    def test_soft_ny_bias_does_not_reject_counter_setup(self):
        engine = Engine(config())
        engine.ny.status = "SELL"
        engine.accept(setup_event())
        engine.accept(tick("4146", 1))
        entries = [e for e in engine.events if e["event"] == "PAPER_ENTRY"]
        self.assertEqual(entries[0]["bias_alignment"], "COUNTER_BIAS")

    def test_daily_guard_blocks_pending_second_entry(self):
        engine = Engine(config())
        engine.accept(setup_event())
        engine.accept(tick("4146", 1))
        engine.daily.halted = True
        engine.accept(tick("4143", 2))
        self.assertEqual(len(engine.positions), 2)
        self.assertIn("S-1", engine.consumed_bos)

    def test_cross_day_open_positions_stay_unresolved(self):
        engine = Engine(config())
        engine.accept(setup_event())
        engine.accept(tick("4146", 1))
        following = tick("4143", 2)
        following["time"] = "2026-10-06T07:00:00Z"
        engine.accept(following)
        self.assertEqual(len(engine.positions), 2)
        self.assertEqual(engine.execution_block, "TODO_STRATEGY_UNRESOLVED:positions_across_daily_reset")

    def test_annotation_no_reverse_without_executed_core(self):
        engine = Engine(config())
        event = setup_event(entries=("4146.5",))
        event["ob"] = ["4141", "4143"]
        engine.accept(event)
        engine.accept(tick("4140", 1))
        engine.accept({"kind": "structure", "time": "2026-10-05T07:00:02Z", "setup_id": "S",
                       "source": "test", "bos_broken": True, "ifvg_confirmed": True})
        self.assertFalse(engine.setups["S"].reverse_armed)

    def test_dual_parent_reversal_remains_unresolved(self):
        engine = Engine(config())
        event = setup_event()
        event["ob"] = ["4141", "4143"]
        for input_event in (event, tick("4146", 1), tick("4143", 2), tick("4140", 3),
                            {"kind": "structure", "time": "2026-10-05T07:00:04Z", "setup_id": "S",
                             "source": "test", "bos_broken": True, "ifvg_confirmed": True}):
            engine.accept(input_event)
        self.assertFalse(engine.setups["S"].reverse_armed)
        self.assertTrue(any("breaker_dual_parent" in e.get("reason", "") for e in engine.events))

    def test_deterministic_journal_and_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "one", Path(directory) / "two"
            for output in (first, second):
                run(ROOT / "tests/canonical-buy.jsonl", ROOT / "configs/fixture.example.json", output)
            for name in ("events.jsonl", "manifest.json"):
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())

    def test_cumulative_profit_does_not_reset_with_the_day(self):
        engine = Engine(config())
        for line in (ROOT / "tests/canonical-buy.jsonl").read_text().splitlines():
            engine.accept(json.loads(line))
        following = tick("4160", 1)
        following["time"] = "2026-10-06T07:00:00Z"
        engine.accept(following)
        self.assertEqual(engine.total_closed_profit, D("38"))
        self.assertEqual(engine.daily.closed_profit, D("0"))
        self.assertEqual(engine.daily_results["2026-10-05"]["closed_profit_usd"], D("38"))

    def test_daily_gross_basis_does_not_discard_net_costs_from_total(self):
        cfg = config()
        cfg["daily_profit_basis"] = "gross"
        cfg["commission_usd_per_lot_per_side"] = "10"
        engine = Engine(cfg)
        for line in (ROOT / "tests/canonical-buy.jsonl").read_text().splitlines():
            engine.accept(json.loads(line))
        self.assertEqual(engine.daily.closed_profit, D("38"))
        self.assertEqual(engine.total_closed_profit, D("37.2"))


class SessionChecks(unittest.TestCase):
    def prepare(self, cfg=None):
        context = NYBias(cfg or config())
        # 07:00 UTC == 10:30 Iran under the explicit fixture offset.
        start = datetime(2026, 10, 5, 7, tzinfo=timezone.utc)
        for i in range(8):
            context.accept(Bar.read(bar_event(i, "4140", "4142", "4138", "4141", "M15", start)))
        return context, start

    def test_ny_wick_threshold_and_both_sides(self):
        context, start = self.prepare()
        context.accept(Bar.read(bar_event(8, "4141", "4145", "4140", "4142", "M15", start)))
        self.assertEqual(context.status, "BUY")
        context.accept(Bar.read(bar_event(9, "4141", "4143", "4135", "4140", "M15", start)))
        self.assertEqual(context.status, "AMBIGUOUS_BOTH_SIDES")

    def test_ny_cutoff_unknown_and_missing_range(self):
        cfg = config()
        cfg["ny_london_scan_end_minute"] = None
        context, start = self.prepare(cfg)
        context.accept(Bar.read(bar_event(8, "4141", "4145", "4140", "4142", "M15", start)))
        self.assertEqual(context.status, "UNRESOLVED")
        context, start = self.prepare()
        context.coverage.remove(630)
        context.accept(Bar.read(bar_event(8, "4141", "4145", "4140", "4142", "M15", start)))
        self.assertEqual(context.status, "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
