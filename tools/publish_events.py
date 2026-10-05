"""Tail a capture/replay journal into the read-only Vercel dashboard.

No orders, no strategy decisions, no clock conversion. Retry the exact batch;
advance the local checkpoint only after the server acknowledges its sequence.
Requires TRADERLAB_INGEST_KEY in the process environment; never logs its value.
"""
import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def publish(endpoint, key, run, events):
    request = urllib.request.Request(endpoint, data=json.dumps({"run": run, "events": events}, ensure_ascii=False).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
    # Never follow a redirect: an ingest key must not travel to another origin.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if 400 <= error.code < 500 and error.code not in (408, 429):
            raise ValueError(f"Ingest rejected batch (HTTP {error.code}); checkpoint unchanged.") from None
        raise OSError(f"Ingest temporarily unavailable (HTTP {error.code})") from None
    except urllib.error.URLError:
        raise OSError("Ingest connection unavailable; checkpoint unchanged.") from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--url", required=True, help="HTTPS dashboard origin, not a secret")
    parser.add_argument("--run", required=True, help="New unique ID for each capture; never reuse for a different file")
    parser.add_argument("--bot", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--source", choices=("native", "paper"), required=True)
    parser.add_argument("--symbol", required=True, help="Exact broker symbol or annotated replay symbol")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--once", action="store_true", help="Upload complete lines and exit; otherwise tail continuously")
    args = parser.parse_args()
    key = os.environ.get("TRADERLAB_INGEST_KEY", "")
    origin = urllib.parse.urlsplit(args.url)
    local = origin.hostname in ("localhost", "127.0.0.1")
    if len(key) < 32 or origin.username or origin.password or origin.query or origin.fragment or origin.path not in ("", "/") or (origin.scheme != "https" and not (local and origin.scheme == "http")):
        parser.error("Supply an HTTPS origin and an environment ingest key of at least 32 characters.")
    if not args.file.is_file():
        parser.error("Capture file does not exist yet. Start the EA capture first.")
    run = {"id": args.run, "bot_id": args.bot, "source": args.source, "label": args.label, "symbol": args.symbol}
    identity = {"file": str(args.file.resolve()), "origin": args.url.rstrip("/"), "run": run}
    state = {**identity, "offset": 0, "seq": 0, "last_line_sha256": None, "last_line_offset": 0}
    if args.checkpoint.exists():
        state = json.loads(args.checkpoint.read_text(encoding="utf-8"))
        if any(state.get(k) != value for k, value in identity.items()):
            parser.error("Checkpoint belongs to another run/file/origin; use a new checkpoint.")
    args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
    retry = 1
    heartbeat_at = 0.0
    print(f"Read-only publisher: {args.run}; source={args.source}. No broker orders.", flush=True)
    while True:
        if args.file.stat().st_size < state["offset"]:
            raise ValueError("Capture truncated; use a new run ID and checkpoint.")
        with args.file.open("rb") as stream:
            if state["last_line_sha256"]:
                stream.seek(state["last_line_offset"])
                if hashlib.sha256(stream.readline()).hexdigest() != state["last_line_sha256"]:
                    raise ValueError("Capture changed at the checkpoint. Refusing to skip or overwrite events.")
            stream.seek(state["offset"])
            events, next_state, size = [], state.copy(), 0
            while len(events) < 100:
                position = stream.tell()
                raw = stream.readline(32_001)
                if not raw or not raw.endswith(b"\n"):
                    if len(raw) > 32_000:
                        raise ValueError("Capture row exceeds the ingest event size limit.")
                    break  # The writer has not completed this line; keep it for the next batch.
                if size + len(raw) > 200_000:
                    break
                try:
                    row = json.loads(raw.decode("utf-8-sig"))
                except (UnicodeError, json.JSONDecodeError):
                    raise ValueError(f"Invalid capture at byte {position}; checkpoint unchanged.") from None
                if type(row.get("seq")) is not int or row["seq"] != next_state["seq"] + 1:
                    raise ValueError(f"Sequence gap at byte {position}; checkpoint unchanged.")
                events.append(row)
                size += len(raw)
                next_state.update(offset=stream.tell(), seq=row["seq"], last_line_offset=position,
                                  last_line_sha256=hashlib.sha256(raw).hexdigest())
        if events or time.monotonic() - heartbeat_at >= 10:
            try:
                result = publish(args.url.rstrip("/") + "/api/ingest", key, run, events)
                if result.get("last_seq") != next_state["seq"]:
                    raise ValueError("Server sequence differs from this capture; refusing to advance.")
                if events:
                    temporary = args.checkpoint.with_name(args.checkpoint.name + ".tmp")
                    temporary.write_text(json.dumps(next_state, sort_keys=True), encoding="utf-8")
                    os.replace(temporary, args.checkpoint)
                    state = next_state
                    print(f"Acknowledged through event {state['seq']}", flush=True)
                heartbeat_at, retry = time.monotonic(), 1
            except OSError as error:
                print(str(error), flush=True)
                if args.once:
                    raise
                time.sleep(retry)
                retry = min(retry * 2, 30)
                continue
        if args.once and not events:
            print("Complete rows uploaded. No incomplete row was consumed.", flush=True)
            break
        if not events:
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Publisher stopped; acknowledged checkpoint preserved.")
    except (ValueError, OSError) as error:
        raise SystemExit(str(error)) from None
