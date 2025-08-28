from __future__ import annotations
import json
from typing import Any, Dict, List
from bs4 import BeautifulSoup

EVENT_TYPES = {
    "Event", "MusicEvent", "TheaterEvent", "ExhibitionEvent", "Festival", "ComedyEvent"
}

def _ensure_list(x):
    if x is None: return []
    return x if isinstance(x, list) else [x]

def extract_events_from_jsonld(html: str) -> List[Dict[str, Any]]:
    """Return list of schema.org Event dicts from HTML. Handles @graph and arrays."""
    out: List[Dict[str, Any]] = []
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(tag.get_text() or "null")
        except Exception:
            continue
        for node in _ensure_list(data):
            if isinstance(node, dict) and "@graph" in node:
                for g in _ensure_list(node["@graph"]):
                    _maybe_add_event(g, out)
            else:
                _maybe_add_event(node, out)
    return out

def _maybe_add_event(node: Dict[str, Any], out: List[Dict[str, Any]]) -> None:
    if not isinstance(node, dict): return
    typ = node.get("@type")
    if isinstance(typ, list):
        is_event = any(t in EVENT_TYPES for t in typ)
    else:
        is_event = typ in EVENT_TYPES
    if not is_event: return
    out.append(node)
