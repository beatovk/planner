from __future__ import annotations

import gzip
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

USER_AGENT = "WeekPlannerBot/1.0 (+https://example.com)"


def should_snapshot(total: int, rank: int, *, top_percent: float) -> bool:
    """
    Return True if item at 'rank' (0-based) falls into the top 'top_percent' of 'total'.
    """
    if total <= 0 or top_percent <= 0.0:
        return False
    from math import ceil
    limit = max(1, ceil(total * top_percent))
    return rank < limit


def build_snapshot_path(event_id: str, dt: datetime, base_dir: str) -> str:
    """
    Build relative path like YYYY/MM/DD/<event_id>.html.gz beneath base_dir.
    Returns the relative path (POSIX style). Caller can join with base_dir.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    rel = f"{dt.year:04d}/{dt.month:02d}/{dt.day:02d}/{event_id}.html.gz"
    # ensure parent exists when saving; here we only compute relative path
    return rel


def save_snapshot(url: str, abs_path: str, *, timeout: float = 8.0) -> None:
    """
    Download HTML and write it gz-compressed to 'abs_path'.
    Raises on network or IO errors. Caller handles exceptions.
    """
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html, */*;q=0.1"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    # be lenient: some sites don't send Content-Type properly
    text = resp.text or ""
    out_path = Path(abs_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out_path, "wt", encoding="utf-8") as gz:
        gz.write(text)
