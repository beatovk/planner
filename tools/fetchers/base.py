from __future__ import annotations
import time
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dtp
from datetime import datetime, timedelta, timezone

UA = "Mozilla/5.0 (compatible; WeekPlanner/1.0; +https://example.local)"
DEFAULT_HTTP_TIMEOUT = 10

def get_html(url: str, *, timeout: int = DEFAULT_HTTP_TIMEOUT, headers: dict | None = None) -> Optional[BeautifulSoup]:
    try:
        r = requests.get(url, headers=(headers or {"User-Agent": UA}), timeout=timeout)
        if r.status_code != 200:
            return None
        return BeautifulSoup(r.text, "lxml")
    except Exception:
        return None

def within_next_7_days(iso_date: str) -> bool:
    # интервал по UTC (достаточно для отсева)
    today = datetime.now(timezone.utc).date()
    end = today + timedelta(days=7)
    try:
        d = dtp.isoparse(iso_date).date()
        return today <= d <= end
    except Exception:
        return False

def within_next_7_days_range(start_iso: str, end_iso: str | None = None) -> bool:
    """
    Проверяет, пересекается ли диапазон событий с окном ближайших 7 дней.
    Если end_iso не указан, проверяет только start_iso.
    """
    today = datetime.now(timezone.utc).date()
    window_end = today + timedelta(days=7)
    
    try:
        start_date = dtp.isoparse(start_iso).date()
        
        # Если указан только start_date, проверяем его
        if not end_iso:
            return today <= start_date <= window_end
        
        # Если указан диапазон, проверяем пересечение
        end_date = dtp.isoparse(end_iso).date()
        return max(today, start_date) <= min(window_end, end_date)
        
    except Exception:
        return False

def parse_date_range(text: str) -> tuple[str|None, str|None]:
    """
    Пытается распарсить диапазон вроде:
    "6 Sep — 7 Dec 2025", "22 Aug - 30 Sep 2025", "13—25 Aug 2025"
    Возвращает (start_iso, end_iso) или (None, None)
    """
    try:
        t = text.replace("–", "-").replace("—", "-")
        parts = [p.strip() for p in t.split("-") if p.strip()]
        if len(parts) == 1:
            d = dtp.parse(parts[0], dayfirst=True).date().isoformat()
            return d, d
        # если год указан только один раз — dateutil поймёт второй по контексту
        start = dtp.parse(parts[0], dayfirst=True).date().isoformat()
        end   = dtp.parse(parts[-1], dayfirst=True).date().isoformat()
        return start, end
    except Exception:
        return None, None

def window_next_7_days() -> tuple[datetime.date, datetime.date]:
    today = datetime.now(timezone.utc).date()
    return today, today + timedelta(days=7)

def ranges_overlap(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    try:
        from dateutil import parser as _p
        sa, ea = _p.isoparse(a_start).date(), _p.isoparse(a_end).date()
        sb, eb = _p.isoparse(b_start).date(), _p.isoparse(b_end).date()
        return max(sa, sb) <= min(ea, eb)
    except Exception:
        return False

def normalize_event(
    title: str,
    date_iso: str,
    url: str,
    source: str,
    category_hint: str = "",
    venue: str | None = None,
    address: str | None = None,
    time_str: str | None = None,
    end_date_iso: str | None = None,
    desc: str | None = None,
    popularity: int | None = None,
    price_min: float | None = None,
    rating: float | None = None,
    subtitle: str | None = None,
    tags: list[str] | None = None,
    image: str | None = None,
) -> Dict:
    return {
        "title": title.strip(),
        "date": date_iso,
        "end": end_date_iso,  # может быть None
        "time": time_str,
        "category": category_hint,
        "venue": (venue or "").strip() or None,
        "address": (address or "").strip() or None,
        "desc": (desc or "").strip() or None,
        "popularity": popularity,     # числовая популярность, если нашли (attending/going/interested)
        "price_min": price_min,       # минимальная цена (THB) если нашли; free -> 0
        "rating": rating,             # если у источника есть оценки (редко)
        "subtitle": (subtitle or "").strip() or None,
        "tags": tags or [],
        "image": image,
        "source": source,
        "url": url
    }

# ==== НОВОЕ: общие функции для работы с интервалами ====
def date_in_range(date_iso: str, start_iso: str, end_iso: str) -> bool:
    try:
        d  = dtp.isoparse(date_iso).date()
        s  = dtp.isoparse(start_iso).date()
        e  = dtp.isoparse(end_iso).date()
        return s <= d <= e
    except Exception:
        return False

def find_best_image(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """
    Ищет лучшее изображение: сначала og:image, затем twitter:image, затем первое img
    """
    # og:image
    og_img = soup.select_one("meta[property='og:image']")
    if og_img and og_img.get("content"):
        img_url = og_img.get("content").strip()
        if img_url.startswith("http"):
            return img_url
        elif img_url.startswith("/"):
            from urllib.parse import urljoin
            return urljoin(base_url, img_url)
    
    # twitter:image
    twitter_img = soup.select_one("meta[name='twitter:image']")
    if twitter_img and twitter_img.get("content"):
        img_url = twitter_img.get("content").strip()
        if img_url.startswith("http"):
            return img_url
        elif img_url.startswith("/"):
            from urllib.parse import urljoin
            return urljoin(base_url, img_url)
    
    # первое img на странице
    img_el = soup.select_one("img")
    if img_el and img_el.get("src"):
        img_url = img_el.get("src").strip()
        if img_url.startswith("http"):
            return img_url
        elif img_url.startswith("/"):
            from urllib.parse import urljoin
            return urljoin(base_url, img_url)
    
    return None
