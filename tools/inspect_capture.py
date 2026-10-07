"""Read-only structural and timestamp checks for a native MT5 JSONL capture."""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from traderlab.broker import diagnose_server_offset, tehran_time, validate_capture_timestamp


CAPABILITY_FIELDS = (
    "broker_symbol", "strategy_pip", "digits", "point", "tick_size", "tick_value_profit",
    "tick_value_loss", "contract_size", "volume_min", "volume_max",
    "volume_step", "volume_limit", "stops_level", "freeze_level", "trade_mode",
    "order_mode", "filling_mode", "account_currency", "account_margin_mode",
    "account_leverage", "account_trade_mode",
    "account_trade_allowed", "account_trade_expert", "account_hedge_allowed",
    "swap_long", "swap_short",
)

# These native events use TimeCurrent(), unlike market events using time_msc.
# Legacy logs have no precision field; only these names with .000 may be coarse.
SECOND_PRECISION_EVENTS = frozenset({
    "EA_INIT", "EA_DEINIT", "BROKER_CAPABILITY_SNAPSHOT", "BROKER_CONFIG_BLOCKED",
    "BROKER_TIME_OFFSET", "CONFIG_UNRESOLVED",
    "TICK_CAPTURE_START", "TICK_CAPTURE_SUMMARY", "TICK_CAPTURE_ERROR", "TICK_CAPTURE_AMBIGUITY",
})

CAPTURE_COUNTERS = (
    "ontick_callbacks", "drain_calls", "copyticks_calls", "emitted_ticks", "callback_snapshot_matches",
    "recovered_ticks", "duplicate_overlap_skips", "cursor_ambiguities", "copyticks_errors",
    "snapshot_errors", "timer_errors",
)


def capture_integer(row, field, minimum=0):
    value = row.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{field} must be an integer >= {minimum}")
    return value


def validate_tick_capture(rows, ticks, errors):
    """Validate recorded loss-aware evidence, not completeness of the broker feed."""
    starts = [row for row in rows if row.get("event") == "TICK_CAPTURE_START"]
    summaries = [row for row in rows if row.get("event") == "TICK_CAPTURE_SUMMARY"]
    if not starts and not summaries:
        return None  # Legacy captures have no CopyTicks evidence.
    if len(starts) != 1 or len(summaries) != 1:
        errors.append("loss-aware capture requires exactly one TICK_CAPTURE_START and final TICK_CAPTURE_SUMMARY")
        return summaries[0] if summaries else None
    start, summary = starts[0], summaries[0]
    try:
        if start.get("capture_version") != "loss_aware_v1" or summary.get("capture_version") != "loss_aware_v1":
            raise ValueError("unknown loss-aware capture version")
        if start.get("startup_policy") != "exclude_baseline_and_earlier_ticks" or \
                start.get("same_millisecond_policy") != "ordered_full_prefix":
            raise ValueError("unknown startup/cursor policy")
        start_msc = capture_integer(start, "cursor_time_msc", 1)
        start_count = capture_integer(start, "cursor_boundary_count", 1)
        capture_integer(start, "timer_interval_ms", 1)
        for row in (start, summary):
            if "broker_feed_complete" not in row or row["broker_feed_complete"] is not None:
                raise ValueError("broker feed completeness must remain unknown (null)")
        counters = {field: capture_integer(summary, field) for field in CAPTURE_COUNTERS}
        if summary.get("terminal_cursor_evidence_valid") is not True or summary.get("capture_halted") is not False:
            raise ValueError("terminal cursor evidence is invalid or capture halted")
        if any(counters[field] for field in ("cursor_ambiguities", "copyticks_errors", "snapshot_errors", "timer_errors")):
            raise ValueError("capture summary reports ambiguity/API/timer errors")
        if counters["emitted_ticks"] != len(ticks) or \
                counters["emitted_ticks"] != counters["recovered_ticks"] + counters["callback_snapshot_matches"]:
            raise ValueError("emitted/recovered/callback summary counters do not reconcile with TICK rows")
        if counters["callback_snapshot_matches"] > counters["ontick_callbacks"] or \
                not 1 <= counters["copyticks_calls"] <= counters["drain_calls"] + 1:
            raise ValueError("callback/CopyTicks counters are inconsistent")
        if [tick.get("tick_index") for tick in ticks] != list(range(1, len(ticks) + 1)):
            raise ValueError("loss-aware tick_index stream must be contiguous from 1")
        previous_msc, previous_ordinal = start_msc, start_count
        for tick in ticks:
            msc = capture_integer(tick, "time_msc", 1)
            ordinal = capture_integer(tick, "millisecond_ordinal", 1)
            if msc < previous_msc or ordinal != (previous_ordinal + 1 if msc == previous_msc else 1):
                raise ValueError("raw tick cursor/ordinal is not chronological or includes startup history")
            if capture_integer(tick, "broker_time_seconds") != msc // 1000:
                raise ValueError("raw tick seconds do not match time_msc")
            utc = validate_capture_timestamp(tick["server_time"], tick["time"], tick["server_utc_offset_seconds"])
            delta = utc - datetime(1970, 1, 1, tzinfo=timezone.utc)
            expected_msc = ((delta.days * 86400 + delta.seconds + tick["server_utc_offset_seconds"]) * 1000
                            + delta.microseconds // 1000)
            if delta.microseconds % 1000 or msc != expected_msc or tick.get("timestamp_precision") != "milliseconds":
                raise ValueError("raw time_msc does not exactly preserve UTC milliseconds")
            capture_integer(tick, "flags")
            capture_integer(tick, "volume")
            decimal(tick["last"], "last")
            if decimal(tick["volume_real"], "volume_real") < 0:
                raise ValueError("volume_real cannot be negative")
            previous_msc, previous_ordinal = msc, ordinal
        if ticks and (capture_integer(summary, "cursor_time_msc", 1) != previous_msc or
                      capture_integer(summary, "cursor_boundary_count", 1) != previous_ordinal):
            raise ValueError("final cursor does not match last emitted tick")
        # Final summary follows ticks/detector observations and precedes only EA_DEINIT.
        summary_index = rows.index(summary)
        if rows.index(start) >= summary_index or [row.get("event") for row in rows[summary_index + 1:]] != ["EA_DEINIT"]:
            raise ValueError("capture summary is not final")
        if any(tick["seq"] <= start["seq"] or tick["seq"] >= summary["seq"] for tick in ticks):
            raise ValueError("TICK row is outside capture boundaries")
        recovered = 0
        last_recovery_index = 0
        for row in rows:
            if row.get("event") != "TICK_CAPTURE_RECOVERY":
                continue
            first = capture_integer(row, "first_tick_index", 1)
            last = capture_integer(row, "last_tick_index", first)
            count = capture_integer(row, "recovered_ticks", 1)
            if row.get("source") not in ("ontick", "timer", "deinit") or \
                    first <= last_recovery_index or last > len(ticks) or count > last - first + 1 or \
                    not ticks[last - 1]["seq"] < row["seq"] < summary["seq"]:
                raise ValueError("recovery diagnostic range/count is invalid")
            recovered += count
            last_recovery_index = last
        if recovered != counters["recovered_ticks"]:
            raise ValueError("recovery events do not reconcile with summary")
    except (KeyError, TypeError, ValueError) as error:
        errors.append(f"invalid loss-aware capture: {error}")
    return summary


def decimal(value, name):
    try:
        parsed = Decimal(str(value))
        if not parsed.is_finite():
            raise ValueError(f"{name} must be finite")
        return parsed
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{name} is not numeric") from None


def inspect_capture(path: Path):
    errors, attention = [], []
    rows = []
    try:
        for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    errors.append(f"line {line_number}: event must be a JSON object")
                    continue
                rows.append(row)
            except json.JSONDecodeError as error:
                errors.append(f"line {line_number}: invalid JSON: {error.msg}")
        if not rows:
            errors.append("capture contains no events")
            return {"rows": rows, "errors": errors, "attention": attention}

        event_counts = Counter(row.get("event") for row in rows)
        if not event_counts["EA_INIT"]:
            errors.append("EA_INIT is missing")
        if not event_counts["CLOSED_BAR"]:
            errors.append("capture contains no CLOSED_BAR rows")
        init = next((row for row in rows if row.get("event") == "EA_INIT"), {})
        if init.get("broker_orders_enabled") is not False:
            errors.append("EA_INIT broker_orders_enabled must be false")
        snapshots = [row for row in rows if row.get("event") == "BROKER_CAPABILITY_SNAPSHOT"]
        if not snapshots:
            errors.append("BROKER_CAPABILITY_SNAPSHOT is missing")
        snapshot = snapshots[0] if snapshots else {}
        symbol = init.get("broker_symbol")
        if not symbol:
            errors.append("EA_INIT broker_symbol is missing")
        if snapshot.get("broker_symbol") != symbol:
            errors.append("capability snapshot symbol differs from EA_INIT")
        for row in rows:
            if row.get("kind") in ("tick", "bar") and row.get("symbol") != symbol:
                errors.append(f"seq {row.get('seq')}: {row.get('kind')} symbol differs from EA_INIT")

        missing = [field for field in CAPABILITY_FIELDS if field not in snapshot]
        if missing:
            errors.append("capability snapshot missing: " + ", ".join(missing))
        if not missing:
            try:
                if decimal(snapshot["strategy_pip"], "strategy_pip") != Decimal("0.1"):
                    raise ValueError("strategy_pip must remain 0.1 XAUUSD price units")
                digits = snapshot["digits"]
                if isinstance(digits, bool) or int(digits) != digits or int(digits) < 0:
                    raise ValueError("digits must be a non-negative integer")
                for field in ("point", "tick_size", "contract_size", "volume_min", "volume_max", "volume_step"):
                    if decimal(snapshot[field], field) <= 0:
                        raise ValueError(f"{field} must be positive")
                if decimal(snapshot["volume_max"], "volume_max") < decimal(snapshot["volume_min"], "volume_min"):
                    raise ValueError("volume_max is below volume_min")
                if decimal(snapshot["volume_limit"], "volume_limit") < 0:
                    raise ValueError("volume_limit cannot be negative")
                for field in ("stops_level", "freeze_level", "trade_mode", "order_mode", "filling_mode",
                              "account_margin_mode", "account_trade_mode"):
                    if int(snapshot[field]) < 0:
                        raise ValueError(f"{field} cannot be negative")
                if int(snapshot["account_leverage"]) <= 0:
                    raise ValueError("account_leverage must be positive")
                for field in ("account_trade_allowed", "account_trade_expert", "account_hedge_allowed"):
                    if not isinstance(snapshot[field], bool):
                        raise ValueError(f"{field} must be boolean")
                for field in ("swap_long", "swap_short"):
                    decimal(snapshot[field], field)
                for field in ("tick_value_profit", "tick_value_loss"):
                    decimal(snapshot[field], field)
                if not isinstance(snapshot["account_currency"], str) or not snapshot["account_currency"]:
                    raise ValueError("account_currency is missing")
            except (ValueError, TypeError, InvalidOperation) as error:
                errors.append(f"invalid capability snapshot: {error}")

        seqs, offsets, ticks, spreads, utc_times, tehran_times = [], [], [], [], [], []
        chronological_floor = None
        second_precision_seqs = []
        for row in rows:
            seq = row.get("seq")
            if isinstance(seq, bool) or not isinstance(seq, int) or seq < 1:
                errors.append(f"invalid event seq: {seq!r}")
            else:
                seqs.append(seq)
            if row.get("time") is None:
                errors.append(f"seq {seq}: canonical UTC timestamp is missing")
                continue
            server_time = row.get("server_time")
            server_offset = row.get("server_utc_offset_seconds")
            tehran_offset = row.get("tehran_utc_offset_seconds")
            if not isinstance(server_time, str) or isinstance(server_offset, bool) or not isinstance(server_offset, int):
                errors.append(f"seq {seq}: server timestamp/offset is unresolved")
                continue
            if isinstance(tehran_offset, bool) or not isinstance(tehran_offset, int):
                errors.append(f"seq {seq}: Tehran offset is unresolved")
                continue
            if tehran_offset != 12600:
                errors.append(f"seq {seq}: first LiteFinance capture requires Tehran UTC+03:30 (12600 seconds)")
            if not isinstance(row["time"], str) or not row["time"].endswith("Z"):
                errors.append(f"seq {seq}: canonical UTC time must end with Z")
                continue
            try:
                if diagnose_server_offset(server_time, server_offset) != "MATCH":
                    raise ValueError("configured server offset does not match documented LiteFinance schedule")
                utc = validate_capture_timestamp(server_time, row["time"], server_offset)
                expected_tehran = tehran_time(utc, tehran_offset).isoformat(timespec="milliseconds")
                if row.get("strategy_time") != expected_tehran:
                    raise ValueError("strategy_time does not match canonical UTC and configured Tehran offset")
            except (ValueError, TypeError) as error:
                errors.append(f"seq {seq}: {error}")
                continue
            offsets.append(server_offset)
            utc_times.append(utc)
            tehran_times.append(row["strategy_time"])

            precision = row.get("timestamp_precision")
            coarse_event = row.get("event") in SECOND_PRECISION_EVENTS
            if precision not in (None, "seconds", "milliseconds"):
                errors.append(f"seq {seq}: unknown timestamp_precision: {precision!r}")
            if precision == "seconds" and (not coarse_event or row.get("kind") in ("tick", "bar") or utc.microsecond):
                errors.append(f"seq {seq}: second precision is invalid for this event/timestamp")
            coarse = (coarse_event and row.get("kind") not in ("tick", "bar") and
                      precision in (None, "seconds") and utc.microsecond == 0)
            # Compare the observed interval [second, second+1s), without rewriting
            # timestamps or lowering the ordering floor set by precise events.
            if coarse:
                second_precision_seqs.append(seq)
                regressed = chronological_floor is not None and utc + timedelta(seconds=1) <= chronological_floor
            else:
                regressed = chronological_floor is not None and utc < chronological_floor
            if regressed:
                errors.append(f"seq {seq}: canonical UTC timestamps are not chronological")
            chronological_floor = max(chronological_floor, utc) if chronological_floor is not None else utc

            if row.get("kind") == "tick":
                ticks.append(row)
                try:
                    bid, ask = decimal(row["bid"], "bid"), decimal(row["ask"], "ask")
                    spread = decimal(row["spread_price"], "spread_price")
                    if ask < bid or spread < 0 or spread != ask - bid:
                        raise ValueError("Bid/Ask/spread are inconsistent or negative")
                    spreads.append(spread)
                except (KeyError, ValueError, TypeError) as error:
                    errors.append(f"seq {seq}: invalid tick quote: {error}")

        if seqs != sorted(set(seqs)):
            errors.append("event seq values are duplicated or not increasing")
        seq_gaps = sum(max(0, current - previous - 1) for previous, current in zip(seqs, seqs[1:]))
        if len(offsets) and len(set(offsets)) != 1:
            errors.append("server UTC offset changed within capture; split captures at offset changes")
        if not ticks:
            errors.append("capture contains no TICK rows")
        tick_indexes = [row.get("tick_index") for row in ticks]
        if any(isinstance(value, bool) or not isinstance(value, int) for value in tick_indexes):
            errors.append("TICK rows contain a missing or invalid tick_index")
        elif tick_indexes != sorted(set(tick_indexes)):
            errors.append("TICK tick_index values are duplicated or not increasing")
        tick_gaps = sum(max(0, current - previous - 1) for previous, current in zip(tick_indexes, tick_indexes[1:])
                        if isinstance(previous, int) and isinstance(current, int))
        for event in ("CONFIG_UNRESOLVED", "BROKER_CONFIG_BLOCKED", "TICK_CAPTURE_ERROR", "TICK_CAPTURE_AMBIGUITY"):
            found = [row for row in rows if row.get("event") == event]
            if found:
                attention.append({"event": event, "count": len(found), "details": found})
                if event in ("TICK_CAPTURE_ERROR", "TICK_CAPTURE_AMBIGUITY"):
                    errors.append(f"{event} present ({len(found)}); terminal-history evidence cannot be accepted")
        tick_capture_summary = validate_tick_capture(rows, ticks, errors)

        return {
            "rows": rows, "errors": errors, "attention": attention,
            "event_counts": event_counts, "symbol": symbol, "snapshot": snapshot,
            "offsets": sorted(set(offsets)), "utc_times": utc_times,
            "tehran_times": tehran_times, "ticks": ticks, "spreads": spreads,
            "seq_gaps": seq_gaps, "tick_gaps": tick_gaps,
            "second_precision_seqs": second_precision_seqs,
            "tick_capture_summary": tick_capture_summary,
        }
    except OSError as error:
        return {"rows": [], "errors": [str(error)], "attention": []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    args = parser.parse_args()
    result = inspect_capture(args.capture)
    print(f"Status: {'FAIL' if result['errors'] else 'PASS'}")
    print(f"Events: {len(result['rows'])}; symbol: {result.get('symbol', 'unknown')}")
    if result.get("event_counts"):
        for name, count in sorted(result["event_counts"].items(), key=lambda item: str(item[0])):
            print(f"  {name}: {count}")
    if result.get("offsets"):
        print(f"Server UTC offset(s): {', '.join(map(str, result['offsets']))}")
    if result.get("utc_times"):
        print(f"UTC observed range: {min(result['utc_times']).isoformat()} to {max(result['utc_times']).isoformat()}")
        print(f"Tehran observed range: {min(result['tehran_times'])} to {max(result['tehran_times'])}")
    if result.get("second_precision_seqs"):
        print(f"Second-precision lifecycle/diagnostic events: {len(result['second_precision_seqs'])}; "
              "checked as one-second intervals; stored timestamps unchanged")
    if result.get("spreads"):
        average = sum(result["spreads"], Decimal(0)) / len(result["spreads"])
        spread_summary = (min(result["spreads"]), average, max(result["spreads"]))
        print("Spread price min/avg/max: " + "/".join(map(str, spread_summary)))
        print("Spread strategy pips min/avg/max: " + "/".join(
            str(value / Decimal("0.1")) for value in spread_summary))
    if result.get("snapshot"):
        print("Capability snapshot:")
        for field in CAPABILITY_FIELDS:
            if field in result["snapshot"]:
                print(f"  {field}: {result['snapshot'][field]}")
    print(f"Event seq gaps: {result.get('seq_gaps', 0)}; tick_index gaps: {result.get('tick_gaps', 0)}")
    if result.get("tick_capture_summary"):
        print("CopyTicks capture summary: " + json.dumps(result["tick_capture_summary"], ensure_ascii=False))
        print("These counters validate terminal-history evidence; broker feed completeness is unknown.")
    else:
        print("No CopyTicks capture summary: legacy capture; contiguous indexes do not prove tick completeness.")
    for row in result["attention"]:
        print(f"ATTENTION {row['event']} ({row['count']}): {json.dumps(row['details'], ensure_ascii=False)}")
    for error in result["errors"]:
        print(f"ERROR: {error}")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
