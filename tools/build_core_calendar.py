"""Build one sourced Sydney->New York day. Never select an overlapping reset policy."""
import argparse
from datetime import date, datetime, time, timezone
import importlib.metadata
import json
from pathlib import Path
from zoneinfo import ZoneInfo


def utc(local_day, local_time, zone):
    return datetime.combine(local_day, time.fromisoformat(local_time), ZoneInfo(zone)).astimezone(timezone.utc)


def build(snapshot, day):
    day = date.fromisoformat(day)
    if day.weekday() >= 5 or not date.fromisoformat(snapshot["day_coverage_start"]) <= day <= date.fromisoformat(snapshot["day_coverage_end"]):
        raise ValueError("Day outside reviewed weekday/holiday coverage")
    if day.isoformat() in snapshot["excluded_days"]:
        raise ValueError("Session holiday not approved")
    known = datetime.fromisoformat(snapshot["observed_at"].replace("Z", "+00:00"))
    if known.utcoffset().total_seconds() != 0:
        raise ValueError("Source observation must be UTC")
    profile = snapshot["session_profile"]
    start = utc(day, profile["sydney_open"], "Australia/Sydney")
    end = utc(day, profile["new_york_close"], "America/New_York")
    news_start = datetime.fromisoformat(snapshot["news_coverage_start"].replace("Z", "+00:00"))
    news_end = datetime.fromisoformat(snapshot["news_coverage_end"].replace("Z", "+00:00"))
    if not news_start <= start < end <= news_end or known >= end:
        raise ValueError("Source coverage/availability cannot certify this day")
    # One DAY only: source-local Sydney/NY windows can overlap on adjacent dates.
    # Coverage is extended through the supplied news horizon, not through more trading days.
    epoch = lambda t: str(int(t.timestamp()))
    lines = [f"SYDNEY_NY_NEWS|{snapshot['source_id']}|{epoch(start)}|{epoch(news_end)}",
             f"DAY|{day.isoformat()}|{epoch(start)}|{epoch(end)}|{epoch(known)}"]
    events = []
    for e in snapshot["events"]:
        if e["name"] not in ("CPI", "NFP", "FOMC") or not e["source"].startswith("https://"):
            raise ValueError("Unsupported or unsourced event")
        at = utc(date.fromisoformat(e["date"]), e["local_time"], "America/New_York")
        if start <= at <= news_end:
            lines.append(f"NEWS|{e['name']}|{epoch(at)}|0|{epoch(known)}")
            events.append({**e, "utc": at.isoformat()})
    manifest = {"day": day.isoformat(), "session_start_utc": start.isoformat(),
                "session_end_utc": end.isoformat(), "news_coverage_end_utc": news_end.isoformat(),
                "observed_at": known.isoformat(), "events_in_coverage": events,
                "tzdata_version": importlib.metadata.version("tzdata"),
                "session_profile": profile, "source_urls": snapshot["source_urls"],
                "scope": "ONE_CONTROLLED_DAY_NO_AUTOMATIC_ROLLOVER",
                "adjacent_day_overlap_policy": None, "broker_execution_enabled": False}
    return "\n".join(lines) + "\n", manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sources", type=Path, required=True)
    p.add_argument("--day", required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    text, manifest = build(json.loads(a.sources.read_text(encoding="utf-8-sig")), a.day)
    a.out.write_text(text, encoding="utf-8")
    a.out.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
