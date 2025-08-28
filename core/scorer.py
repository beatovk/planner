from __future__ import annotations
from typing import Dict, Optional
from datetime import datetime
import math

# весовая модель (можно потом вынести в конфиг)
W = {
    "source": 0.25,
    "popularity": 0.35,
    "price": 0.10,
    "time_slot": 0.08,
    "venue": 0.12,
    "text": 0.08,
    "fresh": 0.02,
}

# простая карта авторитетности источников
SOURCE_WEIGHT = {
    "residentadvisor.net": 1.0,
    "ra.co": 1.0,
    "timeout.com": 0.7,
    "eventbrite.com": 0.6,
    "bangkokartcity.org": 0.8,
    "bacc.or.th": 0.7,
    "housecinema.com": 0.6,
    "majorcineplex.com": 0.6,
}

# престиж площадок (можно расширять)
VENUE_RANK = {
    "bangkok art and culture centre": 1.0,
    "bacc": 1.0,
    "river city bangkok": 0.9,
    "moca": 0.9,
    "chulalongkorn university museum": 0.8,
    "beam": 1.0,
    "mustache": 0.9,
}

TEXT_BONUS_TOKENS = [
    "festival","opening","vernissage","premiere","headliner",
    "live set","label night","exhibition opening","awards","biennale"
]

NIGHT_CATS = {"electronic","nightlife","dj","club","bars","jazz"}

def _norm01(x: float, lo: float, hi: float) -> float:
    if x is None: return 0.0
    if hi<=lo: return 0.0
    x = max(lo, min(hi, x))
    return (x-lo)/(hi-lo)

def _source_score(src: str) -> float:
    if not src: return 0.3
    s = src.lower()
    for key, val in SOURCE_WEIGHT.items():
        if key in s:
            return val
    return 0.4

def _popularity_score(pop: Optional[int]) -> float:
    if pop is None: return 0.0
    # 0 -> 0, 50 -> 0.4, 200 -> 0.8, 500+ -> ~1.0 (лог-норм)
    return _norm01(math.log1p(pop), math.log1p(0), math.log1p(500))

def _price_score(price_min: Optional[float]) -> float:
    if price_min is None: return 0.5  # неизвестно — среднее
    if price_min == 0: return 1.0     # free — бонус
    # чем дороже — тем ниже, но мягко
    return max(0.0, 1.0 - _norm01(price_min, 0, 1200))  # 1200฿ как «дорого»

def _time_slot_score(time_str: Optional[str], category: Optional[str]) -> float:
    t = (time_str or "").lower()
    cat = (category or "").lower()
    evening = any(k in t for k in ["20","21","22","pm","night","late"]) or any(c in cat for c in NIGHT_CATS)
    weekend = False
    # без конкретного дня берём слабый бонус
    base = 0.5 + (0.2 if evening else 0.0) + (0.1 if weekend else 0.0)
    return min(1.0, base)

def _venue_score(venue: Optional[str]) -> float:
    if not venue: return 0.4
    v = venue.lower()
    for key, val in VENUE_RANK.items():
        if key in v:
            return val
    return 0.5

def _text_score(title: str, desc: Optional[str]) -> float:
    txt = (title or "")
    if desc: txt += " " + desc
    txt = txt.lower()
    return 1.0 if any(tok in txt for tok in TEXT_BONUS_TOKENS) else 0.5

def _fresh_score(date_iso: str) -> float:
    # всё уже в выбранном окне; маленький бонус, если сегодня
    try:
        d = datetime.fromisoformat(date_iso).date()
        from datetime import datetime as _dt, timezone as _tz
        today = _dt.now(_tz.utc).date()
        return 1.0 if d == today else 0.5
    except Exception:
        return 0.5

def coolness(e: Dict) -> float:
    s = 0.0
    s += W["source"]     * _source_score(e.get("source"))
    s += W["popularity"] * _popularity_score(e.get("popularity"))
    s += W["price"]      * _price_score(e.get("price_min"))
    s += W["time_slot"]  * _time_slot_score(e.get("time"), e.get("category"))
    s += W["venue"]      * _venue_score(e.get("venue"))
    s += W["text"]       * _text_score(e.get("title",""), e.get("desc"))
    s += W["fresh"]      * _fresh_score(e.get("date"))
    return round(float(s), 4)

def boost(e: dict) -> float:
    s = e.get("_score", 0)
    title = (e.get("title") or "").lower()
    desc = (e.get("desc") or "").lower()
    venue = (e.get("venue") or "").lower()
    tags = " ".join(e.get("tags") or []).lower()

    # boost for keywords
    if any(x in title+desc for x in ["festival","biennale","opening","premiere","awards"]):
        s += 0.3

    # boost for top venues
    if any(x in venue for x in ["bacc", "bangkok art and culture centre", "moca", "river city"]):
        s += 0.2

    # boost if BAC marked as Pick
    if "picks" in tags:
        s += 0.5
    
    # boost for Hot events
    if "hot" in tags:
        s += 0.3

    return round(s, 4)
