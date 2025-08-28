from __future__ import annotations
from typing import Dict, List
import time
from .base import get_html, normalize_event, find_best_image, parse_date_range

ROOT = "https://bk.asia-city.com"

def fetch(cat_id: str = None) -> List[Dict]:
    """
    Фетчер для BK Magazine
    Чек-лист: рубрики Things to do, guide/this weekend, подборки
    Title: article h1, h2, .node__title a
    URL: из заголовка/кнопки «Read more»
    Image: сначала <meta property="og:image">, затем первая article img[src]
    Date: в тексте под заголовком/подписи блока
    Venue: хвост абзаца или подпись
    Description: первый связный <p> после заголовка
    Hot/Picks: Editor's choice, BK Picks → tags += ["Picks"]
    """
    start_time = time.time()
    out = []
    
    # Определяем URL в зависимости от категории
    if cat_id in ["food", "markets_fairs", "yoga_wellness"]:
        urls = [
            f"{ROOT}/food",
            f"{ROOT}/restaurants", 
            f"{ROOT}/events",
            f"{ROOT}/things-to-do-bangkok/news"
        ]
    elif cat_id in ["live_music_gigs", "jazz_blues", "rooftops_bars"]:
        urls = [
            f"{ROOT}/nightlife",
            f"{ROOT}/bars",
            f"{ROOT}/music",
            f"{ROOT}/things-to-do-bangkok/news"
        ]
    elif cat_id in ["workshops", "parks_walks"]:
        urls = [
            f"{ROOT}/events",
            f"{ROOT}/things-to-do",
            f"{ROOT}/attractions",
            f"{ROOT}/things-to-do-bangkok/news"
        ]
    else:
        urls = [
            f"{ROOT}/events",
            f"{ROOT}/food",
            f"{ROOT}/nightlife",
            f"{ROOT}/things-to-do-bangkok/news"
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
            
        # Ищем карточки событий согласно чек-листу
        cards = soup.select("article, .node, .post, .event, .listing")
        
        for card in cards[:20]:  # максимум 20 карточек с одной страницы
            if len(out) >= 40:
                break
                
            try:
                raw_count += 1
                
                # Заголовок согласно чек-листу
                title_el = card.select_one("h1, h2, .node__title a, .title, .post-title")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 5:
                    continue
                
                # Ссылка согласно чек-листу
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
                
                # Изображение согласно чек-листу: сначала og:image, затем первая article img
                image = None
                og_img = detail_soup.select_one("meta[property='og:image']")
                if og_img and og_img.get("content"):
                    image = og_img.get("content").strip()
                if not image:
                    article_img = detail_soup.select_one("article img[src]")
                    if article_img and article_img.get("src"):
                        img_src = article_img.get("src").strip()
                        if img_src.startswith("/"):
                            image = ROOT + img_src
                        elif img_src.startswith("http"):
                            image = img_src
                
                if image:
                    with_image_count += 1
                
                # Дата согласно чек-листу: в тексте под заголовком/подписи блока
                date_str = None
                end_date = None
                
                # Ищем дату в различных местах
                date_selectors = [
                    "time[datetime]", "time", ".date", ".time", ".published",
                    ".submitted", ".created", ".news-date"
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
                if not date_str:
                    text_content = detail_soup.get_text()
                    import re
                    # Паттерны дат: "Jul 6, 2025", "Jun 27–Jul 3"
                    date_patterns = [
                        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b',
                        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}–\d{1,2}\b',
                        r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b'
                    ]
                    
                    for pattern in date_patterns:
                        matches = re.findall(pattern, text_content)
                        if matches:
                            date_str = matches[0]
                            break
                
                if date_str:
                    # Пытаемся распарсить диапазон
                    start_date, end_date = parse_date_range(date_str)
                    if start_date:
                        date_str = start_date
                        with_date_count += 1
                
                # Место проведения согласно чек-листу: хвост абзаца или подпись
                venue = None
                venue_selectors = [
                    ".venue", ".location", ".where", ".address", ".place"
                ]
                
                for selector in venue_selectors:
                    venue_el = detail_soup.select_one(selector)
                    if venue_el:
                        venue_text = venue_el.get_text(strip=True)
                        if venue_text and len(venue_text) > 3:
                            venue = venue_text
                            break
                
                # Фолбэк: ищем в параграфах токены места
                if not venue:
                    p_elements = detail_soup.find_all("p")
                    for p in p_elements:
                        p_text = p.get_text(strip=True)
                        # Ищем токены места: @, запятые, "Bangkok", известные места
                        if any(token in p_text for token in ["@", "Bangkok", "RCB", "BACC", "Beam", "De Commune"]):
                            # Извлекаем последнюю часть с местом
                            parts = p_text.split(",")
                            if len(parts) > 1:
                                venue = parts[-1].strip()
                                break
                
                # Описание согласно чек-листу: первый связный <p> после заголовка
                desc = None
                title_parent = title_el.parent if title_el else None
                if title_parent:
                    # Ищем параграфы после заголовка
                    p_elements = title_parent.find_all("p")
                    for p in p_elements:
                        p_text = p.get_text(strip=True)
                        if p_text and len(p_text) > 50 and len(p_text) < 500:
                            # Проверяем, что это не дата и не место
                            if not any(date_word in p_text.lower() for date_word in ["2024", "2025", "2026", "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]):
                                desc = p_text[:300]
                                break
                
                # Фолбэк: первый осмысленный параграф
                if not desc:
                    p_elements = detail_soup.find_all("p")
                    for p in p_elements:
                        p_text = p.get_text(strip=True)
                        if p_text and len(p_text) > 80 and len(p_text) < 320:
                            desc = p_text[:300]
                            break
                
                # Hot/Picks согласно чек-листу: Editor's choice, BK Picks
                tags = []
                is_pick = False
                
                # Ищем бейджи и пометки
                pick_selectors = [
                    "strong", "em", ".badge", "h6", ".editor-choice", ".bk-picks",
                    ".featured", ".highlight", ".recommended"
                ]
                
                for selector in pick_selectors:
                    elements = detail_soup.select(selector)
                    for el in elements:
                        text = el.get_text(strip=True).lower()
                        if any(keyword in text for keyword in ["editor's pick", "editor's choice", "bk picks", "featured", "highlight", "recommended", "must-see", "essential"]):
                            is_pick = True
                            break
                    if is_pick:
                        break
                
                # Также проверяем в заголовке и описании
                if not is_pick:
                    title_desc = (title + " " + (desc or "")).lower()
                    if any(keyword in title_desc for keyword in ["editor's pick", "editor's choice", "bk picks", "featured", "highlight", "recommended", "must-see", "essential"]):
                        is_pick = True
                
                if is_pick:
                    tags.append("Picks")
                
                # Если нет даты, пропускаем
                if not date_str:
                    continue
                
                out.append(normalize_event(
                    title=title,
                    date_iso=date_str,
                    end_date_iso=end_date,
                    url=event_url,
                    source="bk.asia-city.com",
                    category_hint=cat_id or "events",
                    desc=desc,
                    image=image,
                    venue=venue,
                    tags=tags
                ))
                
            except Exception as e:
                print(f"Error parsing BK Magazine card: {e}")
                continue
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    # Логирование согласно чек-листу
    print(f'{{"fetcher":"bk_magazine","ok":true,"raw":{raw_count},"with_image":{with_image_count},"with_date":{with_date_count},"elapsed_ms":{elapsed_ms}}}')
    
    return out[:40]  # возвращаем максимум 40 событий
