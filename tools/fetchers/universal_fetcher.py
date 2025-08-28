from __future__ import annotations
from typing import Dict, List, Optional
import time
import random
from datetime import datetime, timedelta
from .base import normalize_event

def fetch_all_sources(cat_id: str = None, max_events: int = 50) -> List[Dict]:
    """
    Универсальный фетчер который объединяет все источники
    """
    print(f"🚀 Запускаем универсальный фетчер для категории: {cat_id or 'all'}")
    
    all_events = []
    
    # 1. Time Out Bangkok
    print(f"\n📰 Источник 1: Time Out Bangkok")
    try:
        from .timeout_bkk_simple import fetch as fetch_timeout
        timeout_events = fetch_timeout(cat_id, max_events)
        print(f"   ✅ Получено {len(timeout_events)} событий")
        all_events.extend(timeout_events)
    except Exception as e:
        print(f"   ❌ Ошибка Time Out: {e}")
    
    # 2. BK Magazine
    print(f"\n📰 Источник 2: BK Magazine")
    try:
        from .bk_magazine_simple import fetch as fetch_bk
        bk_events = fetch_bk(cat_id)
        print(f"   ✅ Получено {len(bk_events)} событий")
        all_events.extend(bk_events)
    except Exception as e:
        print(f"   ❌ Ошибка BK Magazine: {e}")
    
    # 3. Zipevent (если нужно)
    # print(f"\n📰 Источник 3: Zipevent")
    # try:
    #     from .zipevent import fetch as fetch_zipevent
    #     zipevent_events = fetch_zipevent(cat_id)
    #     print(f"   ✅ Получено {len(zipevent_events)} событий")
    #     all_events.extend(zipevent_events)
    # except Exception as e:
    #     print(f"   ❌ Ошибка Zipevent: {e}")
    
    # Убираем дубликаты по URL
    unique_events = []
    seen_urls = set()
    
    for event in all_events:
        url = event.get('url', '')
        if url and url not in seen_urls:
            unique_events.append(event)
            seen_urls.add(url)
    
    print(f"\n🎉 Универсальный фетчер завершен!")
    print(f"📊 Всего событий: {len(all_events)}")
    print(f"📊 Уникальных событий: {len(unique_events)}")
    
    return unique_events[:max_events]

def fetch_by_category(cat_id: str, max_events: int = 50) -> List[Dict]:
    """
    Фетчер по конкретной категории
    """
    return fetch_all_sources(cat_id, max_events)

def fetch_all_categories() -> Dict[str, List[Dict]]:
    """
    Фетчер по всем основным категориям
    """
    categories = {
        "food": "Еда и рестораны",
        "markets_fairs": "Рынки и ярмарки", 
        "live_music_gigs": "Живая музыка",
        "jazz_blues": "Джаз и блюз",
        "rooftops_bars": "Руфтопы и бары",
        "workshops": "Воркшопы",
        "parks_walks": "Парки и прогулки",
        "art_culture": "Искусство и культура",
        "shopping": "Шоппинг",
        "wellness": "Велнес и спорт"
    }
    
    results = {}
    
    for cat_id, cat_name in categories.items():
        print(f"\n🎯 Категория: {cat_name} ({cat_id})")
        try:
            events = fetch_by_category(cat_id, max_events=20)
            results[cat_id] = events
            print(f"   📊 Получено {len(events)} событий")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            results[cat_id] = []
    
    return results
