from __future__ import annotations
from typing import Dict, List, Optional
import time
import re
import random
from .base import get_html, normalize_event, parse_date_range

ROOT = "https://www.zipeventapp.com"

def get_zipevent_html(url: str, timeout: int = 20) -> Optional[BeautifulSoup]:
    """
    Получает HTML с улучшенными заголовками для Zipevent
    """
    from bs4 import BeautifulSoup
    import requests
    
    # Ротация User-Agent
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
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
        "Cache-Control": "max-age=0"
    }
    
    # Retry логика
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Создаем сессию для сохранения cookies
            session = requests.Session()
            session.headers.update(headers)
            
            # Добавляем случайную задержку
            time.sleep(random.uniform(2, 5))
            
            r = session.get(url, timeout=timeout)
            if r.status_code != 200:
                print(f"HTTP {r.status_code} for {url}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # exponential backoff
                    continue
                return None
            return BeautifulSoup(r.text, "lxml")
            
        except requests.exceptions.Timeout:
            print(f"Timeout attempt {attempt + 1}/{max_retries} for {url}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None
        except Exception as e:
            print(f"Error fetching {url} (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None
    
    return None

def get_event_urls_from_sitemap() -> List[str]:
    """
    Получает список URL событий из sitemap
    """
    print("📋 Получаем sitemap Zipevent...")
    
    try:
        # Получаем sitemap
        sitemap_url = f"{ROOT}/sitemap.xml"
        soup = get_zipevent_html(sitemap_url)
        
        if not soup:
            print("❌ Не удалось получить sitemap")
            return []
        
        # Ищем все URL событий (паттерн /e/)
        event_urls = []
        for loc in soup.find_all("loc"):
            url = loc.get_text(strip=True)
            if "/e/" in url:
                event_urls.append(url)
        
        print(f"✅ Найдено {len(event_urls)} событий в sitemap")
        return event_urls
        
    except Exception as e:
        print(f"❌ Ошибка при получении sitemap: {e}")
        return []

def parse_event_page(url: str) -> Dict | None:
    """
    Парсит страницу отдельного события
    """
    try:
        print(f"    🔍 Парсим: {url}")
        soup = get_zipevent_html(url)
        if not soup:
            print(f"    ❌ Не удалось получить HTML")
            return None
        
        # Заголовок из title или itemprop="name"
        title = None
        
        # Ищем в itemprop="name" (это работает для Zipevent)
        og_title = soup.select_one("meta[itemprop='name']")
        if og_title:
            title = og_title.get("content", "").strip()
            print(f"    📝 Заголовок из itemprop: {title}")
        
        # Если нет, берем из title
        if not title:
            title_el = soup.select_one("title")
            if title_el:
                title = title_el.get_text(strip=True).replace(" | Zipevent - Inspiration Everywhere", "").strip()
                print(f"    📝 Заголовок из title: {title}")
        
        if not title:
            print(f"    ❌ Заголовок не найден")
            return None
        
        # Описание из itemprop="description" (это работает для Zipevent)
        desc = None
        og_desc = soup.select_one("meta[itemprop='description']")
        if og_desc:
            desc = og_desc.get("content", "").strip()
        
        # Изображение из og:image
        image = None
        og_image = soup.select_one("meta[property='og:image']")
        if og_image:
            image = og_image.get("content", "").strip()
        
        # URL
        event_url = url
        
        # Дата - ищем в тексте страницы
        date_str = None
        end_date = None
        
        # Ищем даты в тексте
        text_content = soup.get_text()
        date_patterns = [
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                date_str = matches[0]
                break
        
        if date_str:
            print(f"    📅 Найдена дата: {date_str}")
            # Пытаемся распарсить диапазон
            start_date, end_date = parse_date_range(date_str)
            if start_date:
                date_str = start_date
                print(f"    📅 Парсированная дата: {date_str}")
                
                # Проверяем что дата в будущем (не старше 2 недель)
                from datetime import datetime, timedelta
                try:
                    event_date = datetime.strptime(start_date, "%Y-%m-%d")
                    today = datetime.now()
                    two_weeks_later = today + timedelta(weeks=2)
                    
                    print(f"    📅 Дата события: {event_date}")
                    print(f"    📅 Сегодня: {today}")
                    print(f"    📅 2 недели вперед: {two_weeks_later}")
                    
                    # Если событие в прошлом или слишком далеко в будущем - пропускаем
                    if event_date < today or event_date > two_weeks_later:
                        print(f"    ❌ Событие вне диапазона 2 недель")
                        return None
                        
                except ValueError:
                    # Если не удалось распарсить дату - пропускаем
                    print(f"    ❌ Не удалось распарсить дату")
                    return None
        else:
            print(f"    ❌ Дата не найдена")
        
        # Место проведения - ищем в тексте
        venue = None
        venue_keywords = ["Bangkok", "Central", "Mall", "Plaza", "Center", "Expo", "Fair", "Market"]
        for keyword in venue_keywords:
            if keyword.lower() in text_content.lower():
                # Ищем предложение с этим ключевым словом
                sentences = re.split(r'[.!?]', text_content)
                for sentence in sentences:
                    if keyword.lower() in sentence.lower():
                        venue = sentence.strip()[:100]
                        break
                if venue:
                    break
        
        # Категория по ключевым словам в заголовке/описании
        category_hint = "events"
        if any(word in title.lower() for word in ["food", "restaurant", "dining"]):
            category_hint = "food"
        elif any(word in title.lower() for word in ["market", "fair", "expo", "festival"]):
            category_hint = "markets_fairs"
        elif any(word in title.lower() for word in ["workshop", "training", "class"]):
            category_hint = "workshops"
        elif any(word in title.lower() for word in ["yoga", "wellness", "health"]):
            category_hint = "yoga_wellness"
        elif any(word in title.lower() for word in ["music", "concert", "party"]):
            category_hint = "live_music_gigs"
        
        # Теги
        tags = []
        if any(word in title.lower() for word in ["food", "restaurant", "dining"]):
            tags.append("Food")
        if any(word in title.lower() for word in ["market", "fair", "expo"]):
            tags.append("Markets")
        if any(word in title.lower() for word in ["workshop", "training"]):
            tags.append("Workshops")
        if any(word in title.lower() for word in ["yoga", "wellness"]):
            tags.append("Wellness")
        if any(word in title.lower() for word in ["music", "concert"]):
            tags.append("Music")
        
        # Если нет даты, пропускаем
        if not date_str:
            return None
        
        return {
            "title": title,
            "date_iso": date_str,
            "end_date_iso": end_date,
            "url": event_url,
            "source": "zipeventapp.com",
            "category_hint": category_hint,
            "desc": desc,
            "image": image,
            "venue": venue,
            "tags": tags
        }
        
    except Exception as e:
        print(f"Error parsing event {url}: {e}")
        return None

def fetch(cat_id: str = None) -> List[Dict]:
    """
    Фетчер для Zipevent на основе sitemap
    Скачиваем sitemap → очередь URL → парсим карточки событий
    """
    print("🚀 Запускаем Zipevent фетчер (sitemap подход)...")
    start_time = time.time()
    
    out = []
    
    # Получаем список URL событий из sitemap
    event_urls = get_event_urls_from_sitemap()
    
    if not event_urls:
        print("❌ Не удалось получить URL событий")
        return []
    
    print(f"📋 Обрабатываем {len(event_urls)} событий...")
    
    # Ограничиваем количество для тестирования
    max_events = 20  # увеличиваем для поиска будущих событий
    event_urls = event_urls[:max_events]
    
    for i, url in enumerate(event_urls):
        if len(out) >= 5:  # лимит на фетчер - было 40, сокращаем до 5
            break
        
        print(f"  📅 Обрабатываем событие {i+1}/{len(event_urls)}: {url.split('/')[-1]}")
        
        try:
            event_data = parse_event_page(url)
            if event_data:
                # Фильтруем по категории, если указана
                if cat_id and cat_id != event_data.get("category_hint"):
                    continue
                
                out.append(normalize_event(**event_data))
                print(f"    ✅ Добавлено: {event_data['title']}")
            else:
                print(f"    ❌ Не удалось распарсить")
        
        except Exception as e:
            print(f"    ❌ Ошибка: {e}")
            continue
        
        # Задержка между запросами
        if i < len(event_urls) - 1:
            delay = random.uniform(2, 4)
            time.sleep(delay)
    
    elapsed = time.time() - start_time
    print(f"🎉 Zipevent фетчер завершен: {len(out)} событий за {elapsed:.1f}с")
    
    return out[:5]  # возвращаем максимум 5 событий - было 40
