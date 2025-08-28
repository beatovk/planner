from __future__ import annotations
from typing import Dict, List
import time
import re
from .base import get_html, normalize_event, find_best_image, parse_date_range

ROOT = "https://housecinema.com"

def fetch(cat_id: str = None) -> List[Dict]:
    """
    Фетчер для House Samyan
    Чек-лист: раздел MOVIE (Now Screening/Coming Soon) — в каждой карточке название и дата
    Title: на /site/Movie — блоки под заголовками, на детали — h1
    URL: ссылка с постера/заголовка
    Image: на детальной — <meta property="og:image"> или постер img
    Date: на листинге рядом с тайтлом («30 Aug 2025»)
    Venue: фиксированное — «House Samyan (Samyan Mitrtown)»
    Description: синопсис на детальной странице (первый <p>)
    Hot/Picks: Tickets nearly sold out/Sold out или премьерный показ
    """
    start_time = time.time()
    out = []
    
    # Для кино используем основные страницы согласно чек-листу
    urls = [
        f"{ROOT}/site/Movie",  # согласно чек-листу
        f"{ROOT}/movies",
        f"{ROOT}/schedule",
        f"{ROOT}/now-showing"
    ]
    
    raw_count = 0
    with_image_count = 0
    with_date_count = 0
    
    for url in urls:
        if len(out) >= 40:  # лимит на фетчер
            break
            
        soup = get_html(url)
        if not soup:
            continue
            
        # Ищем карточки фильмов согласно чек-листу
        cards = soup.select(".movie-card, .movie, .film, .card, .listing, .movie-item")
        
        for card in cards[:20]:  # максимум 20 карточек с одной страницы
            if len(out) >= 40:
                break
                
            try:
                raw_count += 1
                
                # Заголовок согласно чек-листу: на /site/Movie — блоки под заголовками
                title_el = card.select_one("h1, h2, h3, .title, .movie-title, .film-title, .movie-name")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 3:
                    continue
                
                # Ссылка согласно чек-листу: ссылка с постера/заголовка
                link_el = card.select_one("a")
                if not link_el:
                    continue
                event_url = link_el.get("href", "")
                if not event_url:
                    continue
                if event_url.startswith("/"):
                    event_url = ROOT + event_url
                elif not event_url.startswith("http"):
                    continue
                
                # Переходим на детальную страницу для лучшего парсинга
                detail_soup = get_html(event_url)
                if not detail_soup:
                    continue
                
                # Изображение согласно чек-листу: на детальной — og:image или постер img
                image = None
                og_img = detail_soup.select_one("meta[property='og:image']")
                if og_img and og_img.get("content"):
                    image = og_img.get("content").strip()
                if not image:
                    # Ищем постер фильма
                    poster_selectors = [
                        "img[src*='poster']", "img[src*='movie']", "img[src*='film']",
                        ".poster img", ".movie-poster img", ".film-poster img"
                    ]
                    for selector in poster_selectors:
                        poster_img = detail_soup.select_one(selector)
                        if poster_img and poster_img.get("src"):
                            img_src = poster_img.get("src").strip()
                            if img_src.startswith("/"):
                                image = ROOT + img_src
                            elif img_src.startswith("http"):
                                image = img_src
                            break
                
                if image:
                    with_image_count += 1
                
                # Дата согласно чек-листу: на листинге рядом с тайтлом («30 Aug 2025»)
                date_str = None
                end_date = None
                
                # Сначала ищем дату на карточке
                date_el = card.select_one(".date, .time, .when, time, .showtime, .release-date")
                if date_el:
                    date_text = date_el.get_text(strip=True)
                    if date_text and any(year in date_text for year in ["2024", "2025", "2026"]):
                        date_str = date_text
                
                # Если не нашли на карточке, ищем на детальной странице
                if not date_str and detail_soup:
                    date_selectors = [
                        "time[datetime]", "time", ".date", ".time", ".when", ".showtime",
                        ".release-date", ".movie-date", ".film-date"
                    ]
                    
                    for selector in date_selectors:
                        date_el = detail_soup.select_one(selector)
                        if date_el:
                            if date_el.get("datetime"):
                                date_str = date_el.get("datetime")
                                break
                            else:
                                date_text = date_el.get_text(strip=True)
                                if date_text and any(year in date_text for year in ["2024", "2025", "2026"]):
                                    date_str = date_text
                                    break
                
                # Фолбэк: ищем дату в тексте страницы
                if not date_str and detail_soup:
                    text_content = detail_soup.get_text()
                    # Паттерны дат: "30 Aug 2025", "August 30, 2025"
                    date_patterns = [
                        r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b',
                        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b'
                    ]
                    
                    for pattern in date_patterns:
                        matches = re.findall(pattern, text_content, re.IGNORECASE)
                        if matches:
                            date_str = matches[0]
                            break
                
                if date_str:
                    # Пытаемся распарсить диапазон
                    start_date, end_date = parse_date_range(date_str)
                    if start_date:
                        date_str = start_date
                        with_date_count += 1
                
                # Место проведения согласно чек-листу: фиксированное
                venue = "House Samyan (Samyan Mitrtown)"
                
                # Описание согласно чек-листу: синопсис на детальной странице (первый <p>)
                desc = None
                
                # Ищем синопсис в специальных блоках
                synopsis_selectors = [
                    ".synopsis", ".description", ".desc", ".summary", ".plot",
                    ".movie-description", ".film-description"
                ]
                
                for selector in synopsis_selectors:
                    desc_el = detail_soup.select_one(selector)
                    if desc_el:
                        desc_text = desc_el.get_text(strip=True)
                        if desc_text and len(desc_text) > 50:
                            desc = desc_text[:300]
                            break
                
                # Фолбэк: первый осмысленный параграф
                if not desc:
                    p_elements = detail_soup.find_all("p")
                    for p in p_elements:
                        p_text = p.get_text(strip=True)
                        if p_text and len(p_text) > 80 and len(p_text) < 320:
                            # Проверяем, что это не дата и не техническая информация
                            if not any(word in p_text.lower() for word in ["2024", "2025", "2026", "director", "cast", "runtime", "genre"]):
                                desc = p_text[:300]
                                break
                
                # Hot/Picks согласно чек-листу: Tickets nearly sold out/Sold out или премьерный показ
                tags = ["Cinema"]
                is_hot = False
                
                # Ищем статус билетов
                ticket_status = detail_soup.find_all(text=re.compile(r'sold out|nearly sold out|limited|premiere|festival', re.IGNORECASE))
                for text in ticket_status:
                    parent = text.parent
                    if parent:
                        text_content = parent.get_text().lower()
                        if any(status in text_content for status in ["sold out", "nearly sold out", "limited"]):
                            is_hot = True
                            tags.append("Hot")
                            break
                
                # Ищем премьерные показы
                if not is_hot:
                    premiere_text = detail_soup.find_all(text=re.compile(r'premiere|festival|special screening', re.IGNORECASE))
                    for text in premiere_text:
                        parent = text.parent
                        if parent:
                            text_content = parent.get_text().lower()
                            if any(word in text_content for word in ["premiere", "festival", "special screening"]):
                                is_hot = True
                                tags.append("Picks")
                                break
                
                # Если нет даты, пропускаем
                if not date_str:
                    continue
                
                out.append(normalize_event(
                    title=title,
                    date_iso=date_str,
                    end_date_iso=end_date,
                    url=event_url,
                    source="housecinema.com",
                    category_hint=cat_id or "cinema",
                    desc=desc,
                    image=image,
                    venue=venue,
                    tags=tags
                ))
                
            except Exception as e:
                print(f"Error parsing House Samyan card: {e}")
                continue
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    # Логирование согласно чек-листу
    print(f'{{"fetcher":"house_samyan","ok":true,"raw":{raw_count},"with_image":{with_image_count},"with_date":{with_date_count},"elapsed_ms":{elapsed_ms}}}')
    
    return out[:40]  # возвращаем максимум 40 событий
