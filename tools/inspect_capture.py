"""Read-only structural and timestamp checks for a native MT5 JSONL capture."""
import argparse
from collections import Counter
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
        if utc_times != sorted(utc_times):
            errors.append("canonical UTC timestamps are not chronological")
        if not ticks:
            errors.append("capture contains no TICK rows")
        tick_indexes = [row.get("tick_index") for row in ticks]
        if any(isinstance(value, bool) or not isinstance(value, int) for value in tick_indexes):
            errors.append("TICK rows contain a missing or invalid tick_index")
        elif tick_indexes != sorted(set(tick_indexes)):
            errors.append("TICK tick_index values are duplicated or not increasing")
        tick_gaps = sum(max(0, current - previous - 1) for previous, current in zip(tick_indexes, tick_indexes[1:])
                        if isinstance(previous, int) and isinstance(current, int))
        for event in ("CONFIG_UNRESOLVED", "BROKER_CONFIG_BLOCKED"):
            found = [row for row in rows if row.get("event") == event]
            if found:
                attention.append({"event": event, "count": len(found), "details": found})

        return {
            "rows": rows, "errors": errors, "attention": attention,
            "event_counts": event_counts, "symbol": symbol, "snapshot": snapshot,
            "offsets": sorted(set(offsets)), "utc_times": utc_times,
            "tehran_times": tehran_times, "ticks": ticks, "spreads": spreads,
            "seq_gaps": seq_gaps, "tick_gaps": tick_gaps,
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
        print(f"UTC range: {result['utc_times'][0].isoformat()} to {result['utc_times'][-1].isoformat()}")
        print(f"Tehran range: {result['tehran_times'][0]} to {result['tehran_times'][-1]}")
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
    for row in result["attention"]:
        print(f"ATTENTION {row['event']} ({row['count']}): {json.dumps(row['details'], ensure_ascii=False)}")
    for error in result["errors"]:
        print(f"ERROR: {error}")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
