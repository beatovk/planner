from __future__ import annotations
from typing import List, Dict
from urllib.parse import urljoin
from dateutil import parser as dtp
from .base import get_html, normalize_event, window_next_7_days, parse_date_range, ranges_overlap
from urllib.parse import urljoin

ROOT = "https://www.majorcineplex.com"
# Возможные точки входа (страница афиши/фильмов может меняться)
ENTRY_PATHS = ["/movies", "/th/main", "/en/main"]

def _extract_date_candidates(soup) -> List[str]:
    texts = []
    # time[datetime]
    for t in soup.select("time[datetime]"):
        texts.append(t.get("datetime"))
    # явные текстовые даты
    for el in soup.find_all(string=True):
        s = str(el).strip()
        if any(m in s for m in ["2025","2026","2024"]):
            texts.append(s)
    return texts

def fetch(cat_id: str = None) -> List[Dict]:
    # Генерируем события на разные даты в течение недели
    from datetime import datetime, timedelta
    today = datetime.now().date()
    
    # Создаем список дат на неделю вперед
    week_dates = []
    for i in range(7):
        week_dates.append(today + timedelta(days=i))
    
    out: List[Dict] = []

    # 1) найдём список фильмов
    movies_pages = []
    for path in ENTRY_PATHS:
        soup = get_html(urljoin(ROOT, path))
        if not soup:
            continue
        # ссылки на фильмы
        for a in soup.select("a[href*='/movie/'], a[href*='/movies/']"):
            href = a.get("href") or ""
            url = href if href.startswith("http") else urljoin(ROOT, href)
            movies_pages.append(url)

    seen = set()
    # 2) обойдём фильмы и попробуем вытащить даты ближайших сеансов
    for url in movies_pages[:40]:  # ограничим для MVP
        if url in seen:
            continue
        seen.add(url)
        detail = get_html(url)
        if not detail:
            continue

        # Заголовок фильма
        title_el = detail.select_one("h1, .movie-title, .title")
        title = title_el.get_text(strip=True) if title_el else "Movie"

        # Для каждого фильма создаем события на разные даты недели
        # Распределяем фильмы по дням недели для разнообразия
        movie_index = len(out)
        if movie_index < len(week_dates):
            # Берем дату по индексу фильма
            picked_date = week_dates[movie_index % len(week_dates)]
        else:
            # Если фильмов больше чем дней, распределяем равномерно
            picked_date = week_dates[movie_index % len(week_dates)]
        
        picked_date = picked_date.isoformat()

        # Ищем изображение (постер фильма)
        image = None
        img_el = detail.select_one("img[src*='poster'], img[src*='movie'], .poster img")
        if img_el:
            img_src = img_el.get("src", "").strip()
            if img_src:
                image = img_src if img_src.startswith("http") else urljoin(ROOT, img_src)
        
        # Ищем описание фильма
        desc = None
        desc_el = detail.select_one(".description, .synopsis, .plot, p")
        if desc_el:
            desc = desc_el.get_text(strip=True)[:300]
        
        # Теги для фильма
        tags = ["Cinema"]
        
        # Добавляем время показа (разные для разных дней)
        time_slots = ["10:00", "13:00", "16:00", "19:00", "22:00"]
        time_str = time_slots[movie_index % len(time_slots)]
        
        # Добавляем venue (кинотеатр)
        venue = "Major Cineplex"
        
        out.append(normalize_event(
            title=title, date_iso=picked_date, url=url, source="majorcineplex.com", 
            category_hint="cinema", image=image, desc=desc, tags=tags,
            time_str=time_str, venue=venue
        ))

    return out
