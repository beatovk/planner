from __future__ import annotations
from typing import List, Dict, Tuple, Iterable, Optional
from datetime import datetime, timezone
from difflib import SequenceMatcher

try:  # опционально ускоряем фуззи
    from rapidfuzz import fuzz as _rf_fuzz  # type: ignore
    def _ratio(a: str, b: str) -> float:
        return float(_rf_fuzz.ratio(a, b))
except Exception:  # pragma: no cover
    def _ratio(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio() * 100.0

from ..events import Event
from ..utils.text import normalize_text
from ..normalize.image import PLACEHOLDER, verify_image

# Приоритет источников (чем ниже индекс — тем приоритетнее)
SOURCE_PRIORITY = ["timeout_bkk", "bk_magazine"]
_PRIO = {s: i for i, s in enumerate(SOURCE_PRIORITY)}

def _source_rank(src: str) -> int:
    return _PRIO.get((src or "").lower(), len(_PRIO) + 1)

def _order_union(*seqs: Iterable[str]) -> List[str]:
    seen, out = set(), []
    for seq in seqs:
        for x in seq or []:
            x = (x or "").strip().lower()
            if x and x not in seen:
                seen.add(x)
                out.append(x)
    return out

def _pick_desc(candidates: Iterable[Optional[str]]) -> Optional[str]:
    best = None
    best_len = -1
    for d in candidates:
        if not d:
            continue
        txt = normalize_text(d)
        L = len(txt)
        if L > best_len:
            best = txt
            best_len = L
    return best

def _pick_image(urls: Iterable[Optional[str]]) -> Optional[str]:
    # 1) выбросить пустые/плейсхолдеры
    cleaned = [u for u in (urls or []) if u and u != PLACEHOLDER]
    if not cleaned:
        return None
    # 2) если включена проверка — выбрать первый валидный
    for u in cleaned:
        if verify_image(u):
            return u
    # 3) иначе взять первый
    return cleaned[0]

def _pick_primary(events: List[Event]) -> Event:
    # 1) по приоритету источника, 2) по свежести fetched_at
    return sorted(
        events,
        key=lambda e: (_source_rank(e.source), -(e.fetched_at or datetime.now(timezone.utc)).timestamp()),
    )[0]

def _same_day(d1: Optional[datetime], d2: Optional[datetime]) -> bool:
    if not d1 or not d2:
        return False
    return d1.date() == d2.date()

def _same_venue(v1: Optional[str], v2: Optional[str]) -> bool:
    return (normalize_text(v1 or "").lower() == normalize_text(v2 or "").lower()) and bool(v1 or v2)

def _fuzzy_pairs(events: List[Event], threshold: int = 90) -> List[Tuple[int, int]]:
    pairs = []
    titles = [normalize_text(e.title).lower() for e in events]
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            if not _same_day(events[i].start, events[j].start):
                continue
            if not _same_venue(events[i].venue, events[j].venue):
                continue
            if _ratio(titles[i], titles[j]) >= threshold:
                pairs.append((i, j))
    return pairs

def merge_events(events: List[Event]) -> List[Event]:
    """Слить дубли: группировка по identity_key + фуззи-склейка по (title≈, same date/venue)."""
    if not events:
        return []

    # 1) Группировка по identity_key
    groups: Dict[str, List[Event]] = {}
    for e in events:
        groups.setdefault(e.identity_key(), []).append(e)

    merged: List[Event] = []

    # 2) Фуззи-склейка: «рядом стоящих» с тем же днём/площадкой
    # Сначала плоский список «репрезентантов» групп
    reps: List[Event] = [grp[0] for grp in groups.values()]
    pairs = _fuzzy_pairs(reps, threshold=90)
    # Объединяем identity-ключи групп на основе пар
    # Простая DSU-склейка через список индексов
    parent = list(range(len(reps)))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
    for i, j in pairs:
        union(i, j)

    # Построить финальные наборы identity-ключей, которые надо слить
    id_keys = list(groups.keys())
    rep_to_keys: Dict[int, List[str]] = {find(i): [] for i in range(len(reps))}
    for idx, key in enumerate(groups.keys()):
        rep_to_keys[find(idx)].append(key)

    # 3) Слить по каждой итоговой «супергруппе»
    for _, key_list in rep_to_keys.items():
        bucket: List[Event] = []
        for k in key_list:
            bucket.extend(groups[k])
        primary = _pick_primary(bucket)
        others = [e for e in bucket if e is not primary]

        # поля
        all_descs = [getattr(e, "attrs", {}).get("desc_full") or e.desc for e in bucket]
        best_desc = _pick_desc(all_descs)
        best_image = _pick_image([e.image for e in bucket]) or primary.image
        all_tags = _order_union(*[e.tags for e in bucket])
        all_cats = _order_union(*[e.categories for e in bucket])
        all_sources = _order_union([e.source for e in bucket])
        latest_ts = max(e.fetched_at for e in bucket if e.fetched_at)

        # собрать новый Event на базе primary (сохраняем id/url/source primary)
        merged_ev = Event(
            id=primary.id,
            title=primary.title,
            desc=best_desc or primary.desc,
            start=primary.start,
            end=primary.end,
            time_str=primary.time_str,
            venue=primary.venue,
            area=primary.area,
            address=primary.address,
            image=best_image or primary.image,
            url=primary.url,
            price_min=primary.price_min,
            categories=all_cats,
            tags=all_tags,
            source=primary.source,
            fetched_at=latest_ts,
            attrs=dict(primary.attrs or {}),
            raw_html_ref=primary.raw_html_ref,
        )
        # слить булевые attrs: если где-то True — ставим True
        for e in others:
            for k, v in (e.attrs or {}).items():
                if isinstance(v, bool):
                    merged_ev.attrs[k] = bool(merged_ev.attrs.get(k)) or v
        # merged_ids / sources
        merged_ev.attrs["merged_ids"] = _order_union([e.id for e in bucket])
        merged_ev.attrs["sources"] = all_sources

        merged.append(merged_ev)

    return merged
