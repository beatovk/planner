#!/usr/bin/env python
from __future__ import annotations

import argparse
from storage.db import Database


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize WeekPlanner database")
    parser.add_argument("--url", required=True, help="DB URL, e.g. sqlite:///data.db")
    args = parser.parse_args()

    db = Database(args.url)
    db.create_tables()
    print(f"Initialized DB at {args.url}")


if __name__ == "__main__":
    main()
