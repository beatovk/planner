#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.wp_core.utils.flags import events_disabled
from packages.wp_events.aggregator import collect_events


def main() -> None:
    # Check if events are disabled by feature flag
    if events_disabled():
        print("Events QA disabled by WP_DISABLE_EVENTS=1")
        sys.exit(0)
    
    parser = argparse.ArgumentParser(description="Run a quick QA report")
    parser.add_argument("--json", help="Write QA report JSON to this path")
    args = parser.parse_args()

    if args.json:
        os.environ["QA_JSON_OUT"] = args.json
    collect_events()


if __name__ == "__main__":
    main()
