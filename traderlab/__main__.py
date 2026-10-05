import argparse
from pathlib import Path

from .replay import encode, run
import json


def main():
    parser = argparse.ArgumentParser(description="TraderLab deterministic paper replay; no broker orders")
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.events, args.config, args.out)
    except (ValueError, OSError) as error:
        parser.exit(2, f"Replay failed: {error}\n")
    print(json.dumps(encode(result), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

