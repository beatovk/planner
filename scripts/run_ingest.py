#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
import time
import os

# Add the parent directory to Python path to find packages
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from packages.wp_core.utils.flags import events_disabled
from ingest.scheduler import run_ingest_once, start_scheduler


def main() -> None:
    # Check if events are disabled by feature flag
    if events_disabled():
        print("Events ingestion disabled by WP_DISABLE_EVENTS=1")
        sys.exit(0)
    
    parser = argparse.ArgumentParser(description="Run ingestion worker")
    parser.add_argument("--once", action="store_true", help="Run single ingestion pass and exit")
    args = parser.parse_args()

    if args.once:
        run_ingest_once()
    else:
        start_scheduler()
        # keep process alive
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print("Exiting.")


if __name__ == "__main__":
    main()
