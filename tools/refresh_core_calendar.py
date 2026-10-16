"""Run the forward calendar publisher; never submit or approve orders."""
import argparse
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from traderlab.calendar_service import refresh, session, publisher_lock

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--max-age-seconds', type=int, required=True)
    parser.add_argument('--refresh-seconds', type=int, required=True)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.refresh_seconds < args.max_age_seconds <= 3600:
        parser.error('Require 1 <= refresh < maximum age <=3600 seconds')
    profile = json.loads(args.profile.read_text())['session_profile']
    with publisher_lock(args.out.with_suffix('.daemon.lock')):
        while True:
            now = datetime.now(timezone.utc)
            choices = [now.date()+timedelta(days=n) for n in range(-1, 5)]
            day = next(d for d in choices if d.weekday()<5 and session(d, profile)[1]>now)
            try:
                manifest = refresh(args.out, now, day, profile, args.max_age_seconds)
                print(json.dumps({'status': 'PUBLISHED', **manifest}), flush=True)
            except Exception as error:
                print(json.dumps({'status': 'BLOCKED', 'reason': str(error)}), flush=True)
                if args.once:
                    raise SystemExit(2)
            if args.once:
                break
            # A short sleep keeps shutdown/interrupts responsive.
            for _ in range(args.refresh_seconds):
                time.sleep(1)
