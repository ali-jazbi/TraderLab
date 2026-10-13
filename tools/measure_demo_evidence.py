"""Measure real capture spreads and existing broker results. Never selects risk limits."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from traderlab.broker import validate_capture_timestamp


def spread_sample(path, prefix=False):
    counts = Counter()
    digest = hashlib.sha256()
    last_index = last_msc = last_seq = 0
    first = last = None
    summary = None
    size = path.stat().st_size
    used = 0
    with path.open("rb") as f:
        while used < size:
            line = f.readline(size - used)
            if not line.endswith(b"\n"):
                if prefix:
                    break  # Explicit in-progress suffix, not a silently skipped market record.
                raise ValueError("Incomplete raw row")
            used += len(line)
            digest.update(line)
            r = json.loads(line.decode("utf-8-sig"))
            if r["seq"] <= last_seq:
                raise ValueError("Event order regression")
            last_seq = r["seq"]
            if r["event"] == "TICK_CAPTURE_SUMMARY":
                summary = r
            if r["event"] != "TICK":
                continue
            msc = r["time_msc"]
            if r["symbol"] != "XAUUSD_o" or r["tick_index"] != last_index + 1 or msc < last_msc:
                raise ValueError("Wrong symbol or tick coverage/order")
            at = validate_capture_timestamp(r["server_time"], r["time"], r["server_utc_offset_seconds"])
            delta = at - datetime(1970, 1, 1, tzinfo=timezone.utc)
            utc_msc = delta.days * 86400000 + delta.seconds * 1000 + delta.microseconds // 1000
            if delta.microseconds % 1000 or utc_msc != msc - r["server_utc_offset_seconds"] * 1000:
                raise ValueError("Raw tick millisecond timestamp mismatch")
            bid, ask = D(str(r["bid"])), D(str(r["ask"]))
            if not bid.is_finite() or not ask.is_finite() or bid <= 0 or ask < bid:
                raise ValueError("Invalid quote")
            counts[ask - bid] += 1
            last_index, last_msc = r["tick_index"], msc
            if first is None:
                first = r["time"]
            last = r["time"]
    if not counts:
        raise ValueError("No real ticks")
    if not prefix and (not summary or summary["capture_halted"] or
                       not summary["terminal_cursor_evidence_valid"] or summary["emitted_ticks"] != last_index):
        raise ValueError("Complete accepted capture required")
    def percentile(percent):
        rank = (last_index * percent + 99) // 100
        n = 0
        for value, count in sorted(counts.items()):
            n += count
            if n >= rank:
                return str(value)
    return {"source_file": path.name, "prefix_sha256": digest.hexdigest(), "bytes_reviewed": used,
            "unread_incomplete_suffix_bytes": size - used,
            "evidence_scope": "IN_PROGRESS_PREFIX_NOT_COMPLETE_CAPTURE" if prefix else "COMPLETE_CAPTURE",
            "ticks": last_index, "first_utc": first, "last_utc": last,
            "spread_price": {p: percentile(n) for p, n in (("p50", 50), ("p95", 95), ("p99", 99), ("max", 100))},
            "spread_distribution": {str(k): v for k, v in sorted(counts.items())}}


def broker_results(journal, experts):
    # Existing successful tests are read only; they are not repeated or used as signals.
    latency = {"open": [], "close": []}
    actual_deals = {m[0]: (m[1], D(m[2])) for m in re.findall(
        r"deal #(\d+) (buy|sell) 0\.01 XAUUSD_o at ([\d.]+) done", journal)}
    for order, price, elapsed in re.findall(r"order #(\d+) (?:buy|sell) 0\.01 / 0\.01 XAUUSD_o at ([\d.]+) done in ([\d.]+) ms", journal):
        # Closing order IDs differ from the closed position's entry order.
        at = journal.find("order #" + order + " ")
        preceding = journal[:at].rfind("market ")
        closing = "close #" in journal[preceding:at]
        latency["close" if closing else "open"].append(D(elapsed))
    quotes = []
    slippage = []
    pending = None
    for line in experts.splitlines():
        m = re.search(r"TL_DEMO_(?:SMOKE_PREFLIGHT|AUTO_CHECK):.*side=(?:ORDER_TYPE_)?(BUY|SELL).*?(?:observed_)?bid=([\d.]+).*?(?:observed_)?ask=([\d.]+)", line)
        if m:
            pending = (m[1].lower(), D(m[2]), D(m[3]))
            quotes.append(pending[2] - pending[1])
        result = re.search(r"TL_DEMO_(?:SMOKE_ORDER_RESULT|AUTO_ENTRY):.*retcode=10009 deal=(\d+).*?(?:executed_price|price)=([\d.]+)", line)
        if result and pending:
            actual = actual_deals.get(result[1])
            if not actual or actual[0] != pending[0] or actual[1] != D(result[2]):
                raise ValueError("No matching authoritative broker deal")
            requested = pending[2] if pending[0] == "buy" else pending[1]
            slippage.append(abs(actual[1] - requested))
            pending = None
    return {"orders": {k: {"count": len(v), "elapsed_ms": [str(x) for x in v],
                          "max_ms": str(max(v)) if v else None} for k, v in latency.items()},
            "entry_quotes_spread_price": [str(x) for x in quotes],
            "matched_entry_fill_slippage_price": [str(x) for x in slippage],
            "actual_paired_core_orders_measured": 0,
            "limits_approved": False,
            "limitations": ["Three existing entry deals are not a latency/slippage tail bound",
                            "No two-leg Core/BE/restart broker episode in these logs",
                            "Quote spread distribution is not a fill-slippage distribution"]}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--capture", type=Path, required=True)
    p.add_argument("--live-prefix", type=Path)
    p.add_argument("--journal", type=Path, required=True)
    p.add_argument("--experts", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    j, e = a.journal.read_bytes(), a.experts.read_bytes()
    report = {"historical": spread_sample(a.capture),
              "live": spread_sample(a.live_prefix, True) if a.live_prefix else None,
              "broker": broker_results(j.decode("utf-16"), e.decode("utf-16")),
              "journal_sha256": hashlib.sha256(j).hexdigest(),
              "experts_sha256": hashlib.sha256(e).hexdigest(),
              "production_limits": {"pair_max_ms": None, "spread_price": None, "slippage_points": None,
                                    "news_closure_lead_seconds": None}}
    a.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    compact = {**report, "historical": {k:v for k,v in report["historical"].items() if k != "spread_distribution"},
               "live": {k:v for k,v in (report["live"] or {}).items() if k != "spread_distribution"}}
    print(json.dumps(compact, indent=2))
