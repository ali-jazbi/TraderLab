"""Extract replayable closed bars/ticks from a native capture; never infer timestamps."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from traderlab.broker import diagnose_server_offset, validate_capture_timestamp
from tools.inspect_capture import inspect_capture


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    native_rows = [json.loads(line) for line in args.capture.read_text(encoding="utf-8-sig").splitlines()]
    if any(row.get("event") in ("TICK_CAPTURE_START", "TICK_CAPTURE_SUMMARY", "TICK_CAPTURE_ERROR",
                                "TICK_CAPTURE_AMBIGUITY") for row in native_rows):
        inspection = inspect_capture(args.capture)
        if inspection["errors"]:
            raise SystemExit("Loss-aware capture integrity failed: " + "; ".join(inspection["errors"][:5]))
        native_rows = inspection["rows"]  # Normalize the same snapshot that was validated.
    rows = []
    for index, row in enumerate(native_rows, 1):
        if row.get("kind") not in ("bar", "tick"):
            continue
        offset = row.get("server_utc_offset_seconds")
        if row.get("time") is None or not isinstance(offset, int) or isinstance(offset, bool) or \
                not isinstance(row.get("server_time"), str) or \
                (row["kind"] == "bar" and row.get("opened_at") is None):
            raise SystemExit(f"Capture line {index}: broker UTC offset was unresolved; recapture with an explicit offset")
        # Native TLServerIso emits ISO wall time with a fractional-second dot.
        # Pass it through unchanged so milliseconds remain part of the timestamp.
        server_time = row["server_time"]
        diagnostic = diagnose_server_offset(server_time, offset)
        if diagnostic != "MATCH":
            raise SystemExit(f"Capture line {index}: LiteFinance server offset is {diagnostic}; refusing to infer or rewrite historical time")
        try:
            validate_capture_timestamp(server_time, row["time"], offset)
        except (ValueError, TypeError) as error:
            raise SystemExit(f"Capture line {index}: {error}") from None
        row["server_offset_diagnostic"] = diagnostic
        row["event_id"] = f"native-{row['seq']}"
        rows.append(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    if args.output.exists():
        raise SystemExit("Output already exists; choose a new file")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {len(rows)} time-ordered native inputs; no setup zones were inferred")


if __name__ == "__main__":
    main()
