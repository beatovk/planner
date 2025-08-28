from __future__ import annotations
from typing import List, Dict
from urllib.parse import urljoin
from .base import get_html, normalize_event, parse_date_range, ranges_overlap, dtp, within_next_7_days_range

ROOT = "https://www.bangkokartcity.org"
LIST_URL = urljoin(ROOT, "/discover/exhibitions")

def fetch(*, category: str | None = None, cat_id: str | None = None, **_kwargs) -> List[Dict]:
    # игнорируем лишние параметры, работаем как раньше
    return _actual_fetch_impl()

def _actual_fetch_impl() -> List[Dict]:
    soup = get_html(LIST_URL)
    if not soup:
        return []
    out: List[Dict] = []
    for a in soup.select("a[href*='discover-detail/']"):
        href = a.get("href") or ""
        url = href if href.startswith("http") else urljoin(ROOT, href)
        detail = get_html(url)
        if not detail:
            continue
        time_el = detail.select_one("time[datetime]") or detail.find("time")
        date_text = None
        if time_el and (getattr(time_el, "get", lambda k=None: None)("datetime") or time_el.get_text(strip=True)):
            date_text = time_el.get("datetime") or time_el.get_text(strip=True)
        else:
            p = detail.find(string=lambda s: isinstance(s, str) and any(m in s for m in ["2025","2026","2024"]))
            date_text = str(p).strip() if p else None
        if not date_text:
            continue
        s_iso, e_iso = parse_date_range(date_text)
        if not (s_iso and e_iso):
            continue
        title_el = detail.select_one("h1")
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True) or "Exhibition"
        
        # Ищем название музея/галереи (не адрес)
        venue = None
        
        # Список известных музеев и галерей в Бангкоке
        known_venues = [
            "Bangkok Art and Culture Centre", "BACC", "Bangkok Art & Culture Centre",
            "River City Bangkok", "RCB", "RCB Galleria",
            "MOCA Bangkok", "Museum of Contemporary Art",
            "Seacon Square", "Seacon Square Srinakarin",
            "West Eden Gallery", "West Eden",
            "VS Gallery", "VS",
            "Tang Contemporary Art Bangkok", "Tang Contemporary",
            "People's Gallery", "People's gallery",
            "Anantara Siam Bangkok Hotel", "Anantara Siam",
            "MUNx2", "MUNx2 Seacon Square",
            "Sukhumvit 43", "Sukhumvit 43 Gallery"
        ]
        
        # Пробуем найти название в специальных блоках
        venue_el = detail.select_one(".venue, .location, .address, .gallery, .museum")
        if venue_el:
            venue_text = venue_el.get_text(strip=True)
            # Ищем известное название в тексте
            for known in known_venues:
                if known.lower() in venue_text.lower():
                    venue = known
                    break
        
        # Если не нашли, ищем в параграфах
        if not venue:
            p_elements = detail.find_all("p")
            for p in p_elements:
                p_text = p.get_text(strip=True)
                # Ищем известные названия
                for known in known_venues:
                    if known.lower() in p_text.lower():
                        venue = known
                        break
                if venue:
                    break
        
        # Если все еще не нашли, пробуем извлечь из URL или заголовка
        if not venue:
            # Извлекаем из URL
            if "bacc" in url.lower():
                venue = "BACC"
            elif "rcb" in url.lower():
                venue = "RCB Galleria"
            elif "seacon" in url.lower():
                venue = "Seacon Square"
            elif "west-eden" in url.lower():
                venue = "West Eden Gallery"
        
        # Ищем описание события (не сайта)
        desc = None
        
        # Пробуем найти описание в специальных блоках
        # Сначала ищем в блоках с классом content или description
        content_el = detail.select_one(".content, .description, .exhibition-description, .event-description")
        if content_el:
            desc = content_el.get_text(strip=True)[:300]
        
        # Если не нашли, пробуем найти параграфы после заголовка
        if not desc:
            title_parent = title_el.parent if title_el else None
            if title_parent:
                # Ищем параграфы в том же контейнере
                p_elements = title_parent.find_all("p")
                if p_elements:
                    # Берем первый параграф, который не содержит дату
                    for p in p_elements:
                        p_text = p.get_text(strip=True)
                        if p_text and len(p_text) > 20 and not any(date_word in p_text.lower() for date_word in ["2025", "2026", "2024", "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]):
                            desc = p_text[:300]
                            break
        
        # Если все еще нет описания, пробуем найти любой параграф на странице
        if not desc:
            p_elements = detail.find_all("p")
            for p in p_elements:
                p_text = p.get_text(strip=True)
                if p_text and len(p_text) > 30 and not any(site_desc in p_text.lower() for site_desc in ["bangkok art city", "cultural guide", "information hub", "art and cultural events"]):
                    desc = p_text[:300]
                    break
        
        # Ищем изображение
        image = None
        # Сначала пробуем meta og:image
        og_image = detail.select_one("meta[property='og:image']")
        if og_image:
            image = og_image.get("content", "").strip()
        # Затем пробуем meta twitter:image
        if not image:
            twitter_image = detail.select_one("meta[name='twitter:image']")
            if twitter_image:
                image = twitter_image.get("content", "").strip()
        # Затем пробуем первое изображение на странице
        if not image:
            img_el = detail.select_one("img")
            if img_el:
                img_src = img_el.get("src", "").strip()
                if img_src:
                    image = img_src if img_src.startswith("http") else urljoin(ROOT, img_src)
        
        # detect if this is a 'Pick' or featured event (featured by BAC)
        badges = detail.select("h6, .badge, .tags, .featured, .highlight, .recommended, .top, .star, .fire, .hot")
        is_pick = False
        
        for b in badges:
            text = b.get_text(strip=True).lower()
            if any(keyword in text for keyword in ["pick", "featured", "highlight", "recommended", "top", "star", "fire", "hot", "must-see", "essential"]):
                is_pick = True
                break
        
        # Также проверяем в заголовке и описании
        if not is_pick:
            title_desc = (title + " " + (desc or "")).lower()
            if any(keyword in title_desc for keyword in ["featured", "highlight", "recommended", "top", "star", "must-see", "essential"]):
                is_pick = True
        
        # Формируем теги: базовый "Art" + "Picks" если событие помечено
        tags = ["Art"]
        if is_pick:
            tags.append("Picks")
        
        out.append(normalize_event(
            title=title, date_iso=s_iso, end_date_iso=e_iso, url=url,
            source="bangkokartcity.org", category_hint="art", desc=desc, image=image, venue=venue,
            tags=tags
        ))
    return out
