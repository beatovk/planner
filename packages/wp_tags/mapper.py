#!/usr/bin/env python
"""
Category to facets mapping for event queries.
"""

import re
from typing import Dict, Set, List

# Canonical flags used in both events & places
flags_canonical = [
    "electronic_music", "live_music", "jazz_blues", "rooftop",
    "food_dining", "art_exhibits", "workshops", "cinema",
    "markets", "yoga_wellness", "parks",
]

def categories_to_facets(selected_category_ids: list[str]) -> Dict[str, Set[str]]:
    """
    Translate user categories into cache/search facets.
    
    Args:
        selected_category_ids: List of category IDs from user selection
        
    Returns:
        Dict with "flags" and "categories" sets
    """
    # Алиасы для категорий
    category_aliases = {
        "art": {"art_exhibits", "culture"},
        "art_exhibits": {"art", "culture"},
        "culture": {"art", "art_exhibits"},
        "music": {"electronic_music", "live_music_gigs", "jazz_blues"},
        "nightlife": {"electronic_music", "rooftops_bars", "bars"},
        "wellness": {"yoga_wellness", "parks_walks"},
        "food_drinks": {"food", "rooftops_bars"},
        "entertainment": {"cinema", "markets_fairs", "workshops"}
    }
    
    # Флаги для категорий
    category_flags = {
        "art_exhibits": {"art", "culture"},
        "electronic_music": {"music", "nightlife"},
        "live_music_gigs": {"music", "live"},
        "jazz_blues": {"music", "live"},
        "rooftops_bars": {"nightlife", "food_drinks"},
        "food": {"food_drinks"},
        "workshops": {"entertainment", "learning"},
        "cinema": {"entertainment"},
        "markets_fairs": {"entertainment", "shopping"},
        "yoga_wellness": {"wellness", "health"},
        "parks_walks": {"wellness", "outdoor"}
    }
    
    # Собираем все флаги и категории
    flags: Set[str] = set()
    categories: Set[str] = set()
    
    for cat_id in selected_category_ids:
        cat_id_lower = cat_id.lower()
        
        # Добавляем основную категорию
        categories.add(cat_id_lower)
        
        # Добавляем флаги для категории
        if cat_id_lower in category_flags:
            flags.update(category_flags[cat_id_lower])
        
        # Добавляем алиасы
        if cat_id_lower in category_aliases:
            categories.update(category_aliases[cat_id_lower])
            # Для алиасов тоже добавляем флаги
            for alias in category_aliases[cat_id_lower]:
                if alias in category_flags:
                    flags.update(category_flags[alias])
    
    return {
        "flags": flags,
        "categories": categories
    }


def fallback_flags(selected_category_ids: List[str], facets: Dict[str, Set[str]]) -> Set[str]:
    """
    Гарантирует ненулевой набор флагов для кэширования/поиска.
    1) если facets.flags не пуст — вернуть их;
    2) иначе: попытаться взять пересечение выбранных категорий с KNOWN_FLAGS;
    3) иначе: фолбэк 'all'.
    """
    flags: Set[str] = set(facets.get("flags") or [])
    if flags:
        return flags
    cats = set(facets.get("categories") or [])
    # эвристика: любые категории, содержащие 'art', считаем арт-флагом
    if any("art" in c for c in cats):
        return {"art"}
    # абсолютный фолбэк — общий ключ кэша дня
    return {"all"}


def get_cache_key(city: str, date: str, flag: str) -> str:
    """
    Generate Redis cache key for events.
    
    Args:
        city: City name (e.g., "bangkok")
        date: Date in YYYY-MM-DD format
        flag: Flag name (e.g., "art", "music")
        
    Returns:
        Cache key in format: v2:<city>:<date>:flag:<flag>
    """
    return f"v2:{city.lower()}:{date}:flag:{flag.lower()}"


def get_index_key(city: str, date: str) -> str:
    """
    Generate Redis index key for date.
    
    Args:
        city: City name (e.g., "bangkok")
        date: Date in YYYY-MM-DD format
        
    Returns:
        Index key in format: v2:<city>:<date>:index
    """
    return f"v2:{city.lower()}:{date}:index"


# Универсальный маппер событий в флаги
CATEGORY_RULES = {
    "electronic_music": ["electronic", "dj", "club"],
    "live_music": ["live music", "gig", "band"],
    "jazz_blues": ["jazz", "blues"],
    "rooftop": ["rooftop", "view", "skybar", "bar"],
    "food_dining": ["food", "thai food", "street food", "dining", "restaurant"],
    "art_exhibits": ["art", "exhibition", "gallery", "museum"],
    "workshops": ["workshop", "learning", "craft", "class", "course"],
    "cinema": ["cinema", "movie", "film", "screening"],
    "markets": ["market", "mall", "shopping", "bazaar", "fair"],
    "yoga_wellness": ["yoga", "meditation", "wellness", "retreat"],
    "parks": ["park", "walk", "nature", "outdoor", "garden"],
}

def map_event_to_flags(event: dict) -> list[str]:
    """
    Универсальный маппинг событий → флаги на основе контента.
    
    Args:
        event: Словарь события с полями title, description, tags
        
    Returns:
        Отсортированный список флагов для события
    """
    text = " ".join([
        str(event.get("title", "")).lower(),
        str(event.get("description", "")).lower(),
        " ".join(event.get("tags") or []),
    ])

    flags = []
    for flag, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                flags.append(flag)
                break  # нашли хотя бы одно слово → ставим категорию

    return sorted(set(flags))


def categories_to_place_flags(category_ids: List[str]) -> Dict[str, set]:
    """
    Map category IDs to place flags.
    
    Args:
        category_ids: List of category IDs
        
    Returns:
        Dictionary with "flags" and "categories" sets
    """
    # Use the existing categories_to_facets function
    return categories_to_facets(category_ids)


def map_place_to_flags(place: dict) -> list[str]:
    """
    Универсальный маппинг мест → флаги на основе контента.
    
    Args:
        place: Словарь места с полями name, description, tags, flags
        
    Returns:
        Отсортированный список флагов для места
    """
    # Если у места уже есть флаги, используем их
    if place.get("flags"):
        return sorted(set(place["flags"]))
    
    text = " ".join([
        str(place.get("name", "")).lower(),
        str(place.get("description", "")).lower(),
        " ".join(place.get("tags") or []),
    ])

    flags = []
    for flag, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                flags.append(flag)
                break  # нашли хотя бы одно слово → ставим категорию

    return sorted(set(flags))
