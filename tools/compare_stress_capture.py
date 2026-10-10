"""Read-only exact normal/stress emitted-occurrence comparison; never repairs captures."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.inspect_capture import capture_integer, inspect_capture


def tester_metadata(result, stress):
    rows = result["rows"]
    configs = [r for r in rows if r.get("event") == "TESTER_STRESS_CONFIG"]
    summaries = [r for r in rows if r.get("event") == "TESTER_STRESS_SUMMARY"]
    starts = [r for r in rows if r.get("event") == "TICK_CAPTURE_START"]
    if len(configs) != 1 or len(summaries) != 1 or len(starts) != 1:
        raise ValueError("requires one tester stress config/summary and capture start per file")
    config, summary, start = configs[0], summaries[0], starts[0]
    for row in (config, summary):
        if row.get("environment") != "strategy_tester" or row.get("enabled") is not stress:
            raise ValueError("normal must be tester stress=false; stress must be tester stress=true")
    if config.get("policy") != "skip_n_drain_one_after_baseline" or config.get("timer_policy") != "hold_during_skips":
        raise ValueError("unknown stress scheduling policy")
    if not config["seq"] < start["seq"] < summary["seq"] < result["tick_capture_summary"]["seq"]:
        raise ValueError("tester stress diagnostics are outside startup/final capture boundaries")
    callbacks = capture_integer(summary, "callbacks_seen", 1)
    skipped = capture_integer(summary, "skipped_callbacks")
    timers = capture_integer(summary, "deferred_timer_calls")
    if callbacks != result["tick_capture_summary"]["ontick_callbacks"]:
        raise ValueError("stress scheduler callbacks do not reconcile with capture callbacks")
    if stress:
        skip_limit = capture_integer(config, "skip_callbacks", 1)
        whole, remainder = divmod(callbacks - 1, skip_limit + 1)
        if skipped != whole * skip_limit + min(remainder, skip_limit) or skipped == 0:
            raise ValueError("stress must skip the configured callbacks after the common baseline")
        if result["tick_capture_summary"]["recovered_ticks"] <= 0:
            raise ValueError("stress recovered_ticks must be > 0")
    elif skipped != 0 or timers != 0:
        raise ValueError("normal tester capture must not skip callbacks or hold timers")
    return start, summary


def compare_captures(normal_path, stress_path):
    errors = []
    results = [inspect_capture(Path(normal_path)), inspect_capture(Path(stress_path))]
    for name, result in zip(("normal", "stress"), results):
        errors.extend(f"{name}: {error}" for error in result["errors"])
        if result.get("attention"):
            errors.append(f"{name}: blocked/unresolved/error diagnostic present")
        if not result.get("tick_capture_summary"):
            errors.append(f"{name}: requires loss-aware capture evidence")
    report = {"status": "FAIL", "errors": errors}
    if errors:
        return report
    try:
        normal_start, normal_meta = tester_metadata(results[0], False)
        stress_start, stress_meta = tester_metadata(results[1], True)
        baseline_fields = ("cursor_time_msc", "cursor_boundary_count", "startup_policy",
                           "same_millisecond_policy", "capture_version")
        if any(normal_start.get(k) != stress_start.get(k) for k in baseline_fields):
            raise ValueError("startup baselines differ; no trimming/alignment is permitted")
        if normal_meta["callbacks_seen"] != stress_meta["callbacks_seen"]:
            raise ValueError("tester callback totals differ; rerun with identical test settings/data")
        sequences = []
        for result in results:
            ticks = result["ticks"]
            # Raw-identical repeats are legitimate when their occurrence ordinals differ.
            positions = [(t["time_msc"], t["millisecond_ordinal"]) for t in ticks]
            if len(positions) != len(set(positions)):
                raise ValueError("duplicate emitted terminal-history occurrence")
            sequences.append([{k: v for k, v in tick.items() if k != "seq"} for tick in ticks])
        if len(sequences[0]) != len(sequences[1]):
            raise ValueError(f"emitted tick counts differ: {len(sequences[0])} vs {len(sequences[1])}")
        for index, (normal, stress) in enumerate(zip(*sequences), 1):
            if normal != stress:
                raise ValueError(f"emitted tick sequence differs at tick_index {index}")
        digest = hashlib.sha256(json.dumps(sequences[0], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        report.update(status="PASS", emitted_ticks=len(sequences[0]), tick_sequence_sha256=digest,
                      duplicate_occurrences=0, skipped_callbacks=stress_meta["skipped_callbacks"],
                      deferred_timer_calls=stress_meta["deferred_timer_calls"],
                      normal_recovered_ticks=results[0]["tick_capture_summary"]["recovered_ticks"],
                      stress_recovered_ticks=results[1]["tick_capture_summary"]["recovered_ticks"])
    except (KeyError, TypeError, ValueError) as error:
        errors.append(str(error))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("normal", type=Path)
    parser.add_argument("stress", type=Path)
    args = parser.parse_args()
    report = compare_captures(args.normal, args.stress)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
