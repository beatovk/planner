from typing import List, Optional, Dict, Iterable
import re

# Маппинг редакторских меток на нормализованные теги
EDITOR_LABELS = {
    "editor's pick": "editors_pick",
    "editor pick": "editors_pick",
    "featured": "featured",
    "recommended": "recommended",
    "top pick": "top_pick",
    "must see": "must_see",
    "highlight": "highlight",
}

def _lower_strip_all(items: Iterable[str]) -> List[str]:
    """Нормализует все строки к нижнему регистру и убирает пробелы."""
    return [i.strip().lower() for i in items if isinstance(i, str) and i.strip()]

def enrich_tags(tags: Optional[List[str]], editor_labels: Optional[List[str]] = None) -> List[str]:
    """
    Дополняет список тегов, сохраняя порядок.
    - нормализуем к нижнему регистру
    - уникализируем в порядке первого появления
    - добавляем mapped editor labels в конец, если их ещё нет
    """
    base = _lower_strip_all(tags or [])
    seen = set()
    result: List[str] = []
    
    # Добавляем базовые теги в порядке первого появления
    for t in base:
        if t not in seen:
            seen.add(t)
            result.append(t)
    
    # Добавляем editor labels в конец, если их ещё нет
    for label in _lower_strip_all(editor_labels or []):
        mapped = EDITOR_LABELS.get(label)
        if mapped and mapped not in seen:
            seen.add(mapped)
            result.append(mapped)
    
    return result

def infer_attrs(title: str, desc: Optional[str] = None) -> Dict[str, bool]:
    """
    Извлекает атрибуты из title и description.
    Возвращает словарь с boolean флагами.
    """
    text = f"{title} {desc or ''}".lower()
    
    attrs = {
        "streetfood": False,
        "market": False,
        "rooftop": False,
        "outdoor": False,
        "indoor": False,
        "live_music": False,
        "art": False,
        "culture": False,
    }
    
    # Street food patterns
    if any(word in text for word in ["street food", "street food", "food truck", "hawker", "vendor"]):
        attrs["streetfood"] = True
    
    # Market patterns
    if any(word in text for word in ["market", "bazaar", "souk", "ตลาด", "talat"]):
        attrs["market"] = True
    
    # Rooftop patterns
    if any(word in text for word in ["rooftop", "roof top", "sky bar", "terrace", "balcony"]):
        attrs["rooftop"] = True
    
    # Outdoor patterns
    if any(word in text for word in ["outdoor", "outside", "garden", "park", "beach", "river"]):
        attrs["outdoor"] = True
    
    # Indoor patterns
    if any(word in text for word in ["indoor", "inside", "museum", "gallery", "theater", "cinema"]):
        attrs["indoor"] = True
    
    # Live music patterns
    if any(word in text for word in ["live music", "concert", "gig", "band", "jazz", "rock", "dj"]):
        attrs["live_music"] = True
    
    # Art patterns
    if any(word in text for word in ["art", "exhibition", "gallery", "museum", "painting", "sculpture"]):
        attrs["art"] = True
    
    # Culture patterns
    if any(word in text for word in ["culture", "traditional", "heritage", "festival", "ceremony"]):
        attrs["culture"] = True
    
    return attrs
