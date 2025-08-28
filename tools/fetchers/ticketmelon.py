from __future__ import annotations
from typing import Dict, List
import time
import re
from .base import get_html, normalize_event, find_best_image, parse_date_range

ROOT = "https://www.ticketmelon.com"

def fetch(cat_id: str = None) -> List[Dict]:
    """
    Фетчер для Ticketmelon
    Чек-лист: детальные страницы событий
    Title: h1 (часто — сразу в hero)
    URL: текущая
    Image: <meta property="og:image">; если пусто — article img[src], .banner img
    Date/Range: искать блоки с лейблами Date:/Time:; селекторы вида div:contains("Date") → соседний span/p
    Venue: div:contains("Venue") → следующий a|span
    Description: блок «About/Description», обычно section, .desc, .description
    Price: искать «Free» или числа; div:contains("Tickets"), «Start from … THB»
    Popularity/Hot: текстовые бейджи «Hot», «Trending», «Sold out», «Limited»
    """
    start_time = time.time()
    out = []
    
    # Определяем URL в зависимости от категории
    if cat_id in ["electronic_music", "live_music_gigs", "jazz_blues"]:
        urls = [
            f"{ROOT}/events/music",
            f"{ROOT}/events/concerts",
            f"{ROOT}/events/parties"
        ]
    elif cat_id in ["rooftops_bars"]:
        urls = [
            f"{ROOT}/events/nightlife",
            f"{ROOT}/events/bars",
            f"{ROOT}/events/parties"
        ]
    else:
        urls = [
            f"{ROOT}/events",
            f"{ROOT}/events/featured",
            f"{ROOT}/events/trending"
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
            
        # Ищем карточки событий
        cards = soup.select(".event-card, .event, .card, .listing, a[href*='/events/']")
        
        for card in cards[:20]:  # максимум 20 карточек с одной страницы
            if len(out) >= 40:
                break
                
            try:
                raw_count += 1
                
                # Заголовок
                title_el = card.select_one("h1, h2, h3, .title, .event-title")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 5:
                    continue
                
                # Ссылка
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
                
                # Изображение согласно чек-листу: сначала og:image, затем article img, .banner img
                image = None
                og_img = detail_soup.select_one("meta[property='og:image']")
                if og_img and og_img.get("content"):
                    image = og_img.get("content").strip()
                if not image:
                    article_img = detail_soup.select_one("article img[src], .banner img")
                    if article_img and article_img.get("src"):
                        img_src = article_img.get("src").strip()
                        if img_src.startswith("/"):
                            image = ROOT + img_src
                        elif img_src.startswith("http"):
                            image = img_src
                
                if image:
                    with_image_count += 1
                
                # Дата согласно чек-листу: искать блоки с лейблами Date:/Time:
                date_str = None
                end_date = None
                
                # Ищем блоки с лейблами Date: или Time:
                date_blocks = detail_soup.find_all(text=re.compile(r'Date:|Time:', re.IGNORECASE))
                for block in date_blocks:
                    parent = block.parent
                    if parent:
                        # Ищем соседний элемент с датой
                        next_sibling = parent.find_next_sibling()
                        if next_sibling:
                            date_text = next_sibling.get_text(strip=True)
                            if date_text and any(year in date_text for year in ["2024", "2025", "2026"]):
                                date_str = date_text
                                break
                
                # Фолбэк: ищем в стандартных селекторах
                if not date_str:
                    date_selectors = [
                        "time[datetime]", "time", ".date", ".time", ".when", ".event-date"
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
                    # Паттерны дат: "26 November 2024", "22 June 2025"
                    date_patterns = [
                        r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
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
                
                # Место проведения согласно чек-листу: div:contains("Venue") → следующий a|span
                venue = None
                
                # Ищем блоки с лейблом Venue:
                venue_blocks = detail_soup.find_all(text=re.compile(r'Venue:', re.IGNORECASE))
                for block in venue_blocks:
                    parent = block.parent
                    if parent:
                        # Ищем следующий элемент с названием места
                        next_sibling = parent.find_next_sibling()
                        if next_sibling:
                            venue_text = next_sibling.get_text(strip=True)
                            if venue_text and len(venue_text) > 3:
                                venue = venue_text
                                break
                
                # Фолбэк: стандартные селекторы
                if not venue:
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
                
                # Описание согласно чек-листу: блок «About/Description»
                desc = None
                desc_selectors = [
                    ".description", ".desc", ".about", ".event-description",
                    "section .description", ".content .description"
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
                            desc = p_text[:300]
                            break
                
                # Цена согласно чек-листу: искать «Free» или числа
                price_min = None
                
                # Ищем блоки с лейблом Tickets или ценой
                price_blocks = detail_soup.find_all(text=re.compile(r'Tickets|Price|Cost|THB|฿', re.IGNORECASE))
                for block in price_blocks:
                    parent = block.parent
                    if parent:
                        # Ищем числа в тексте
                        text = parent.get_text()
                        # Ищем "Free"
                        if "free" in text.lower():
                            price_min = 0.0
                            break
                        # Ищем числа с THB
                        price_match = re.search(r'(\d+(?:,\d+)*)\s*THB', text, re.IGNORECASE)
                        if price_match:
                            price_str = price_match.group(1).replace(',', '')
                            try:
                                price_min = float(price_str)
                                break
                            except ValueError:
                                pass
                
                # Фолбэк: ищем в стандартных селекторах цены
                if price_min is None:
                    price_selectors = [
                        ".price", ".cost", ".ticket-price", ".ticket", ".cost"
                    ]
                    for selector in price_selectors:
                        price_el = detail_soup.select_one(selector)
                        if price_el:
                            price_text = price_el.get_text(strip=True).lower()
                            if "free" in price_text:
                                price_min = 0.0
                                break
                            # Ищем числа
                            price_match = re.search(r'(\d+(?:,\d+)*)', price_text)
                            if price_match:
                                price_str = price_match.group(1).replace(',', '')
                                try:
                                    price_min = float(price_str)
                                    break
                                except ValueError:
                                    pass
                
                # Popularity/Hot согласно чек-листу: текстовые бейджи
                tags = []
                popularity = None
                
                # Ищем бейджи популярности
                hot_keywords = ["hot", "trending", "sold out", "limited", "popular"]
                is_hot = False
                
                # Ищем в бейджах и лейблах
                hot_selectors = [
                    ".badge", ".tag", ".label", ".status", ".hot", ".trending"
                ]
                
                for selector in hot_selectors:
                    elements = detail_soup.select(selector)
                    for el in elements:
                        text = el.get_text(strip=True).lower()
                        if any(keyword in text for keyword in hot_keywords):
                            is_hot = True
                            tags.append("Hot")
                            break
                    if is_hot:
                        break
                
                # Ищем числовые показатели популярности
                popularity_text = detail_soup.find_all(text=re.compile(r'views|interested|going|attending', re.IGNORECASE))
                for text in popularity_text:
                    parent = text.parent
                    if parent:
                        # Ищем числа рядом
                        text_content = parent.get_text()
                        number_match = re.search(r'(\d+(?:,\d+)*)', text_content)
                        if number_match:
                            try:
                                popularity = int(number_match.group(1).replace(',', ''))
                                break
                            except ValueError:
                                pass
                
                # Если нет даты, пропускаем
                if not date_str:
                    continue
                
                out.append(normalize_event(
                    title=title,
                    date_iso=date_str,
                    end_date_iso=end_date,
                    url=event_url,
                    source="ticketmelon.com",
                    category_hint=cat_id or "events",
                    desc=desc,
                    image=image,
                    venue=venue,
                    price_min=price_min,
                    popularity=popularity,
                    tags=tags
                ))
                
            except Exception as e:
                print(f"Error parsing Ticketmelon card: {e}")
                continue
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    # Логирование согласно чек-листу
    print(f'{{"fetcher":"ticketmelon","ok":true,"raw":{raw_count},"with_image":{with_image_count},"with_date":{with_date_count},"elapsed_ms":{elapsed_ms}}}')
    
    return out[:40]  # возвращаем максимум 40 событий
