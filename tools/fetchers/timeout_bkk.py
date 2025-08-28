from __future__ import annotations
from typing import Dict, List, Optional
import time
import re
import random
from .base import get_html, normalize_event, parse_date_range

ROOT = "https://www.timeout.com/bangkok"

def get_timeout_html(url: str, timeout: int = 15) -> Optional[BeautifulSoup]:
    """
    Получает HTML с улучшенными заголовками для Time Out
    """
    from bs4 import BeautifulSoup
    import requests
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
        "Referer": ROOT
    }
    
    try:
        session = requests.Session()
        session.headers.update(headers)
        time.sleep(random.uniform(1, 3))
        
        r = session.get(url, timeout=timeout)
        if r.status_code != 200:
            print(f"HTTP {r.status_code} for {url}")
            return None
        return BeautifulSoup(r.text, "lxml")
        
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def fetch(cat_id: str = None) -> List[Dict]:
    """
    Фетчер для Time Out Bangkok
    Чек-лист: ежемесячные/недельные подборки («The best things to do in Bangkok this July», «this weekend»)
    Title: h2 a или блок карточки с «Read more»
    URL: ссылка «Read more»
    Image: внутри блока есть <img>; на детальной странице — <meta property="og:image">
    Date/Range: текст после заголовка (часто прямо строка: «July 4–6», «Until Aug 3») — регулярка + parse_date_range()
    Venue: конец описательного абзаца («RCB Galleria 4, River City Bangkok»), парсить токены
    Description: первый абзац подпункта либо первый <p> на детальной статье
    Hot/Picks: у Time Out бывают «Editor's pick», «Best of the month/week» — ловим strong/em/badge
    """
    start_time = time.time()
    out = []
    
    # Определяем URL в зависимости от категории согласно чек-листу
    if cat_id in ["food", "markets_fairs", "yoga_wellness"]:
        urls = [
            f"{ROOT}/food-and-drink",
            f"{ROOT}/restaurants",
            f"{ROOT}/bars-and-pubs",
            f"{ROOT}/things-to-do/this-weekend",  # еженедельные подборки
            f"{ROOT}/things-to-do/this-month"     # ежемесячные подборки
        ]
    elif cat_id in ["live_music_gigs", "jazz_blues", "rooftops_bars"]:
        urls = [
            f"{ROOT}/bars-and-pubs",
            f"{ROOT}/nightlife",
            f"{ROOT}/music",
            f"{ROOT}/things-to-do/this-weekend",
            f"{ROOT}/things-to-do/this-month"
        ]
    elif cat_id in ["workshops", "parks_walks"]:
        urls = [
            f"{ROOT}/things-to-do",
            f"{ROOT}/attractions",
            f"{ROOT}/shopping",
            f"{ROOT}/things-to-do/this-weekend",
            f"{ROOT}/things-to-do/this-month"
        ]
    else:
        urls = [
            f"{ROOT}/things-to-do",
            f"{ROOT}/events",
            f"{ROOT}/food-and-drink",
            f"{ROOT}/things-to-do/this-weekend",
            f"{ROOT}/things-to-do/this-month"
        ]
    
    raw_count = 0
    with_image_count = 0
    with_date_count = 0
    
    for url in urls:
        if len(out) >= 40:  # лимит на фетчер
            break
            
        soup = get_html(url)
        if not soup:
            print(f"Failed to get HTML from {url}")
            continue
            
        # Ищем карточки событий согласно чек-листу
        cards = soup.select(".card, .event-card, .listing-card, article, .article-card, .feature-card")
        
        for card in cards[:20]:  # максимум 20 карточек с одной страницы
            if len(out) >= 40:
                break
                
            try:
                raw_count += 1
                
                # Заголовок согласно чек-листу: h2 a или блок карточки с «Read more»
                title_el = card.select_one("h1, h2, h3, .title, .card-title, .article-title")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 5:
                    continue
                
                # Ссылка согласно чек-листу: ссылка «Read more»
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
                
                # Изображение согласно чек-листу: внутри блока есть <img>; на детальной странице — og:image
                image = None
                # Сначала ищем на детальной странице
                og_img = detail_soup.select_one("meta[property='og:image']")
                if og_img and og_img.get("content"):
                    image = og_img.get("content").strip()
                
                # Если не нашли, ищем в карточке
                if not image:
                    card_img = card.select_one("img")
                    if card_img and card_img.get("src"):
                        img_src = card_img.get("src").strip()
                        if img_src.startswith("/"):
                            image = ROOT + img_src
                        elif img_src.startswith("http"):
                            image = img_src
                
                if image:
                    with_image_count += 1
                
                # Дата согласно чек-листу: текст после заголовка (часто прямо строка: «July 4–6», «Until Aug 3»)
                date_str = None
                end_date = None
                
                # Ищем дату в карточке
                date_el = card.select_one(".date, .time, .when, time, .event-date, .article-date")
                if date_el:
                    date_text = date_el.get_text(strip=True)
                    if date_text and any(year in date_text for year in ["2024", "2025", "2026"]):
                        date_str = date_text
                
                # Если не нашли в карточке, ищем на детальной странице
                if not date_str and detail_soup:
                    date_selectors = [
                        "time[datetime]", "time", ".date", ".time", ".when", ".event-date",
                        ".article-date", ".published-date"
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
                
                # Фолбэк: ищем дату в тексте страницы согласно чек-листу
                if not date_str and detail_soup:
                    text_content = detail_soup.get_text()
                    # Паттерны дат: «July 4–6», «Until Aug 3», «4–6 July»
                    date_patterns = [
                        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}–\d{1,2}\b',
                        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b',
                        r'\b\d{1,2}–\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b',
                        r'\b(?:Until|Until|From)\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\b'
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
                
                # Место проведения согласно чек-листу: конец описательного абзаца, парсить токены
                venue = None
                
                # Ищем в специальных блоках
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
                
                # Фолбэк: ищем в параграфах токены места согласно чек-листу
                if not venue:
                    p_elements = detail_soup.find_all("p")
                    for p in p_elements:
                        p_text = p.get_text(strip=True)
                        # Ищем токены места: известные места в Бангкоке
                        if any(token in p_text for token in ["RCB Galleria", "River City Bangkok", "BACC", "Beam", "De Commune", "UOB Live", "Samyan Mitrtown"]):
                            # Извлекаем часть с местом
                            for token in ["RCB Galleria", "River City Bangkok", "BACC", "Beam", "De Commune", "UOB Live", "Samyan Mitrtown"]:
                                if token in p_text:
                                    venue = token
                                    break
                            if venue:
                                break
                
                # Описание согласно чек-листу: первый абзац подпункта либо первый <p> на детальной статье
                desc = None
                
                # Ищем в специальных блоках
                desc_selectors = [
                    ".description", ".desc", ".about", ".excerpt", ".summary",
                    ".article-content", ".content"
                ]
                
                for selector in desc_selectors:
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
                            # Проверяем, что это не дата и не место
                            if not any(word in p_text.lower() for word in ["2024", "2025", "2026", "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]):
                                desc = p_text[:300]
                                break
                
                # Hot/Picks согласно чек-листу: у Time Out бывают «Editor's pick», «Best of the month/week»
                tags = []
                is_pick = False
                
                # Ищем бейджи и пометки
                pick_selectors = [
                    "strong", "em", ".badge", ".tag", ".label", ".featured",
                    ".editor-pick", ".best-of", ".highlight", ".recommended"
                ]
                
                for selector in pick_selectors:
                    elements = detail_soup.select(selector)
                    for el in elements:
                        text = el.get_text(strip=True).lower()
                        if any(keyword in text for keyword in ["editor's pick", "best of", "featured", "highlight", "recommended", "must-see", "essential", "top pick"]):
                            is_pick = True
                            tags.append("Picks")
                            break
                    if is_pick:
                        break
                
                # Также проверяем в заголовке и описании
                if not is_pick:
                    title_desc = (title + " " + (desc or "")).lower()
                    if any(keyword in title_desc for keyword in ["editor's pick", "best of", "featured", "highlight", "recommended", "must-see", "essential", "top pick"]):
                        is_pick = True
                        tags.append("Picks")
                
                # Если нет даты, пропускаем
                if not date_str:
                    continue
                
                out.append(normalize_event(
                    title=title,
                    date_iso=date_str,
                    end_date_iso=end_date,
                    url=event_url,
                    source="timeout.com/bangkok",
                    category_hint=cat_id or "events",
                    desc=desc,
                    image=image,
                    venue=venue,
                    tags=tags
                ))
                
            except Exception as e:
                print(f"Error parsing Time Out Bangkok card: {e}")
                continue
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    # Логирование согласно чек-листу
    print(f'{{"fetcher":"timeout_bkk","ok":true,"raw":{raw_count},"with_image":{with_image_count},"with_date":{with_date_count},"elapsed_ms":{elapsed_ms}}}')
    
    return out[:40]  # возвращаем максимум 40 событий
