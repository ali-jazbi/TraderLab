"""Extract replayable closed bars/ticks from a native capture; never infer timestamps."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from traderlab.broker import diagnose_server_offset, server_to_utc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = []
    for index, line in enumerate(args.capture.read_text(encoding="utf-8-sig").splitlines(), 1):
        row = json.loads(line)
        if row.get("kind") not in ("bar", "tick"):
            continue
        offset = row.get("server_utc_offset_seconds")
        if row.get("time") is None or not isinstance(offset, int) or isinstance(offset, bool) or \
                not isinstance(row.get("server_time"), str) or \
                (row["kind"] == "bar" and row.get("opened_at") is None):
            raise SystemExit(f"Capture line {index}: broker UTC offset was unresolved; recapture with an explicit offset")
        server_time = row["server_time"].replace(".", "-", 2)
        diagnostic = diagnose_server_offset(server_time, offset)
        if diagnostic != "MATCH":
            raise SystemExit(f"Capture line {index}: LiteFinance server offset is {diagnostic}; refusing to infer or rewrite historical time")
        expected_utc = server_to_utc(server_time, offset)
        recorded_utc = datetime.fromisoformat(row["time"].replace("Z", "+00:00"))
        if recorded_utc.replace(microsecond=0) != expected_utc:
            raise SystemExit(f"Capture line {index}: recorded UTC does not match server timestamp plus configured offset")
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
