from __future__ import annotations
from typing import List, Dict, Optional
from pathlib import Path
import hashlib
import json
import time
import os
from dateutil import parser as dtp
# Старые fetcher'ы отключены - используем только новые из core/fetchers/
# from tools.fetchers import resident_advisor, timeout_bkk
# from tools.fetchers import bangkok_art_city  # art aggregator
# from tools.fetchers import major_cineplex    # cinema single-source
# from tools.fetchers import timeout_bkk, bk_magazine, zipevent, ticketmelon, house_samyan

from tools.fetchers.base import date_in_range, ranges_overlap

# Маппинг источников на новые fetcher'ы из core/fetchers/
from core.fetchers import BKMagazineFetcher, DatabaseFetcher, EventbriteBKKFetcher

# Временно включаем старые fetcher'ы для art_exhibits
from tools.fetchers import bangkok_art_city

FETCHER_MAP = {
    # Старые fetcher'ы (временно для art_exhibits)
    "bangkok_art_city": lambda cat_id=None: bangkok_art_city.fetch(),
    
    # Новые fetчеры
    "bk_magazine": lambda cat_id=None: BKMagazineFetcher().fetch(category=cat_id),
    "database": lambda cat_id=None: DatabaseFetcher().fetch(category=cat_id),
    "eventbrite_bkk": lambda cat_id=None: EventbriteBKKFetcher().fetch(category=cat_id),
}

CACHE_DIR = Path(".cache_live_v2")
CACHE_TTL_SEC = 2 * 60 * 60  # 2 часа
MAX_EVENTS_TOTAL = 60         # жёсткий потолок на ответ
TARGET_MIN_PER_CATEGORY = 12  # как только набрали около 12 по категории — можно ранний выход

def fetch_from_source(source_id: str, category_id: Optional[str] = None) -> List[Dict]:
    """
    Получить события из указанного источника
    
    Args:
        source_id: ID источника (например, "resident_advisor")
        category_id: ID категории (для источников, которые поддерживают фильтрацию)
    
    Returns:
        Список событий в стандартном формате
    """
    if source_id not in FETCHER_MAP:
        print(f"Source {source_id} not found in FETCHER_MAP")
        return []
    
    try:
        print(f"Fetching from {source_id} for category {category_id}")
        fetcher_func = FETCHER_MAP[source_id]
        events = fetcher_func(category_id)
        print(f"Got {len(events)} events from {source_id}")
        return events
    except Exception as e:
        print(f"Error fetching from {source_id}: {e}")
        return []

def fetch_from_sources(source_ids: List[str], category_id: Optional[str] = None) -> List[Dict]:
    """
    Получить события из нескольких источников
    
    Args:
        source_ids: Список ID источников
        category_id: ID категории (если применимо)
    
    Returns:
        Объединенный список событий
    """
    all_events = []
    for source_id in source_ids:
        events = fetch_from_source(source_id, category_id)
        all_events.extend(events)
    
    return all_events

def get_available_sources() -> List[str]:
    """Получить список доступных источников"""
    return list(FETCHER_MAP.keys())

def _cache_key(source_map: Dict[str, List[str]], category_ids: List[str], date_from: str | None = None, date_to: str | None = None) -> str:
    """Создать ключ кэша для комбинации источников, категорий и дат"""
    data = json.dumps({
        "sources": source_map, 
        "categories": sorted(category_ids),
        "date_from": date_from,
        "date_to": date_to
    }, sort_keys=True)
    return hashlib.md5(data.encode()).hexdigest()

def _cache_get(key: str) -> Optional[List[Dict]]:
    """Получить данные из кэша"""
    try:
        if not CACHE_DIR.exists():
            return None
        cache_file = CACHE_DIR / f"{key}.json"
        if not cache_file.exists():
            return None
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        if time.time() - data.get("timestamp", 0) > CACHE_TTL_SEC:
            return None
        return data.get("events", [])
    except Exception:
        return None

def _cache_set(key: str, events: List[Dict]) -> None:
    """Сохранить данные в кэш"""
    try:
        CACHE_DIR.mkdir(exist_ok=True)
        cache_file = CACHE_DIR / f"{key}.json"
        data = {
            "timestamp": time.time(),
            "events": events
        }
        cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def load_source_map(sources_path) -> Dict[str, List[str]]:
    """Загрузить карту источников из JSON файла"""
    import json
    try:
        with open(sources_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading sources: {e}")
        return {}

def fetch_for_categories(source_map: Dict[str, List[str]], category_ids: List[str],
                         date_from: str | None = None, date_to: str | None = None) -> List[Dict]:
    """
    Получить события для указанных категорий из соответствующих источников
    
    Args:
        source_map: Карта категорий к источникам
        category_ids: Список ID категорий
        date_from: Начальная дата для фильтрации (ISO формат)
        date_to: Конечная дата для фильтрации (ISO формат)
    
    Returns:
        Список событий
    """
    key = _cache_key(source_map, category_ids, date_from, date_to)
    cached = _cache_get(key)
    if cached is not None:
        return cached
    
    events: List[Dict] = []
    seen = set()
    
    for cid in category_ids:
        print(f"Processing category: {cid}")
        cat_count_before = len(events)
        sources_for_cat = source_map.get(cid, [])
        print(f"Sources for {cid}: {sources_for_cat}")
        
        for fetcher_id in sources_for_cat:
            print(f"Processing fetcher: {fetcher_id}")
            fn = FETCHER_MAP.get(fetcher_id)
            if not fn:
                print(f"Fetcher {fetcher_id} not found")
                continue
            print(f"Calling fetcher {fetcher_id} for category {cid}")
            try:
                if fn.__code__.co_argcount > 0:
                    batch = fn(cat_id=cid)
                else:
                    batch = fn()
                print(f"Got {len(batch)} events from {fetcher_id}")
                if not batch:
                    print(f"WARNING: {fetcher_id} returned empty batch")
                else:
                    print(f"  First event: {batch[0].get('title', 'No title')[:50]}...")
                    print(f"  Event keys: {[(e.get('title', '')[:20], e.get('date', 'No date'), str(e.get('url', ''))[:20]) for e in batch[:2]]}")
            except Exception as e:
                print(f"ERROR calling fetcher {fetcher_id}: {e}")
                print(f"Exception type: {type(e).__name__}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                batch = []
            
            for e in batch:
                key2 = (e.get("title"), e.get("date"), e.get("url"))
                if key2 in seen:
                    print(f"  Skipping duplicate: {key2[0][:30]}...")
                    continue
                seen.add(key2)
                events.append(e)
                print(f"  Added event: {e.get('title', 'No title')[:30]}... (total: {len(events)})")
                if len(events) >= MAX_EVENTS_TOTAL:
                    _cache_set(key, events)
                    return events
        # если по этой категории уже собрали ~12 — идём дальше, не копаем глубже
        if len(events) - cat_count_before >= TARGET_MIN_PER_CATEGORY:
            continue
    
    events = events[:MAX_EVENTS_TOTAL]
    print(f"Final events count: {len(events)}")
    
    # Логируем если кэш пустой
    if not events:
        print(f"WARNING: Empty cache written for key: {key}")
        print(f"Cache data: sources={source_map}, categories={category_ids}, date_from={date_from}, date_to={date_to}")
    
    _cache_set(key, events)
    return events
