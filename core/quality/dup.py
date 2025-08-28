from __future__ import annotations

from typing import List, Tuple

try:
    from rapidfuzz import fuzz
except Exception:  # pragma: no cover
    fuzz = None
    from difflib import SequenceMatcher

from ..events import Event
from ..utils.text import normalize_text


def _ratio(a: str, b: str) -> float:
    if fuzz:
        return fuzz.ratio(a, b)
    return SequenceMatcher(None, a, b).ratio() * 100


def find_duplicates(
    events: List[Event], threshold: int = 90
) -> Tuple[List[List[Event]], List[Tuple[Event, Event]]]:
    """Locate duplicates by identity_key and fuzzy-title matches."""
    by_key = {}
    for event in events:
        by_key.setdefault(event.identity_key(), []).append(event)
    dup_groups = [grp for grp in by_key.values() if len(grp) > 1]

    fuzzy_pairs: List[Tuple[Event, Event]] = []
    titles = [
        (normalize_text(e.title).lower(), e.identity_key(), e) for e in events
    ]
    for i in range(len(titles)):
        t1, k1, e1 = titles[i]
        for j in range(i + 1, len(titles)):
            t2, k2, e2 = titles[j]
            if k1 == k2:
                continue
            if _ratio(t1, t2) >= threshold:
                fuzzy_pairs.append((e1, e2))

    return dup_groups, fuzzy_pairs
