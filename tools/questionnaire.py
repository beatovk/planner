from __future__ import annotations
from typing import List, Dict, Set
import json
from pathlib import Path

ALLOWED_TAGS: Set[str] = {
    "jazz","live music","bar",
    "electronic","dj","club","nightlife",
    "art","exhibition","gallery","museum",
    "workshop","learning","crafts","education",
    "food","thai food","street food","tom-yum","spicy","restaurant",
    "rooftop","view","cocktails",
    "park","walks","nature","cycling",
    "market","mall","shopping",
    "theater","performance","show","dance",
    "cinema","movie","screening","indie film",
    "mixology",
    "yoga","meditation","wellness","spa"
}

def load_categories(path: Path) -> List[Dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    for item in data:
        item["tags"] = [t for t in item.get("tags", []) if t in ALLOWED_TAGS]
    return data

def selected_ids_to_tags(categories: List[Dict], selected_ids: List[str]) -> List[str]:
    by_id = {c["id"]: c for c in categories}
    tags: Set[str] = set()
    for cid in selected_ids:
        if cid in by_id:
            tags.update(by_id[cid].get("tags", []))
    return sorted(tags)
