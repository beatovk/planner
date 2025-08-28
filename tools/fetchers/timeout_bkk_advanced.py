from __future__ import annotations
from typing import Dict, List, Optional
import time
import re
import random
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from .base import normalize_event, parse_date_range

ROOT = "https://www.timeout.com/bangkok"

class TimeOutAdvancedFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            # Desktop Chrome
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            
            # Desktop Firefox
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            
            # Mobile Safari
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            
            # Mobile Chrome
            "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        ]
        
    def get_headers(self, referer=None):
        """Генерирует реалистичные заголовки"""
        ua = random.choice(self.user_agents)
        is_mobile = "Mobile" in ua or "iPhone" in ua or "iPad" in ua
        
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,th;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none" if not referer else "same-origin",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        
        if referer:
            headers["Referer"] = referer
            
        if is_mobile:
            headers["Sec-CH-UA-Mobile"] = "?1"
            headers["Viewport-Width"] = "390"
        else:
            headers["Sec-CH-UA-Mobile"] = "?0"
            headers["Sec-CH-UA"] = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
            headers["Sec-CH-UA-Platform"] = '"Windows"'
            
        return headers
    
    def smart_delay(self):
        """Человеко-подобные задержки"""
        delay = random.uniform(3, 8)  # 3-8 секунд
        print(f"    ⏱️ Задержка {delay:.1f}с...")
        time.sleep(delay)
    
    def get_html(self, url: str, method=1) -> Optional[BeautifulSoup]:
        """
        Получает HTML разными методами:
        method 1: Обычный запрос с ротацией UA
        method 2: С предварительным заходом на главную
        method 3: Mobile UA
        method 4: С cookies от главной страницы
        """
        print(f"    🌐 Метод {method}: {url}")
        
        try:
            if method == 2:
                # Сначала заходим на главную для получения cookies
                main_headers = self.get_headers()
                main_resp = self.session.get(ROOT, headers=main_headers, timeout=15)
                print(f"    🏠 Главная страница: {main_resp.status_code}")
                time.sleep(random.uniform(2, 4))
                
            if method == 3:
                # Принудительно используем mobile UA
                mobile_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
                headers = self.get_headers(ROOT)
                headers["User-Agent"] = mobile_ua
            else:
                headers = self.get_headers(ROOT if method > 1 else None)
            
            self.smart_delay()
            
            resp = self.session.get(url, headers=headers, timeout=20)
            print(f"    📊 Ответ: {resp.status_code} ({len(resp.text)} символов)")
            
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, "lxml")
            elif resp.status_code in [403, 429]:
                print(f"    🚫 Блокировка {resp.status_code}")
                return None
            else:
                print(f"    ❌ HTTP {resp.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"    ⏰ Timeout")
            return None
        except Exception as e:
            print(f"    ❌ Ошибка: {e}")
            return None
    
    def try_all_methods(self, url: str) -> Optional[BeautifulSoup]:
        """Пробует все методы по очереди"""
        for method in range(1, 5):
            soup = self.get_html(url, method)
            if soup:
                print(f"    ✅ Метод {method} сработал!")
                return soup
            print(f"    ❌ Метод {method} не сработал")
        
        print(f"    💀 Все методы failed для {url}")
        return None

def is_fresh_event(date_str: str) -> bool:
    """Проверяет что событие в ближайшие 2 недели"""
    if not date_str:
        return False
        
    try:
        event_date = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.now()
        two_weeks_later = today + timedelta(weeks=2)
        
        # Событие должно быть в будущем, но не более чем через 2 недели
        return today <= event_date <= two_weeks_later
    except:
        return False

def fetch(cat_id: str = None) -> List[Dict]:
    """
    Продвинутый фетчер для Time Out Bangkok
    Использует множественные методы обхода блокировок
    """
    print("🚀 Запускаем продвинутый Time Out Bangkok фетчер...")
    start_time = time.time()
    
    fetcher = TimeOutAdvancedFetcher()
    out = []
    
    # Разные URL для разных категорий
    if cat_id == "food":
        urls = [f"{ROOT}/food-and-drink"]
    elif cat_id in ["live_music_gigs", "electronic_music"]:
        urls = [f"{ROOT}/music-and-nightlife"]
    elif cat_id == "art_galleries":
        urls = [f"{ROOT}/art-and-culture"]
    else:
        urls = [
            f"{ROOT}/things-to-do",
            f"{ROOT}/whats-on",
            f"{ROOT}/events"
        ]
    
    for url_idx, url in enumerate(urls):
        if len(out) >= 5:  # лимит для тестирования
            break
            
        print(f"\n📋 Страница {url_idx + 1}/{len(urls)}: {url}")
        
        soup = fetcher.try_all_methods(url)
        if not soup:
            continue
            
        # Ищем карточки событий с разными селекторами
        selectors = [
            "article",
            ".card",
            ".listing", 
            ".event-card",
            ".item",
            "[data-testid*='card']",
            ".article-card",
            ".content-card"
        ]
        
        cards = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                cards = found
                print(f"    🎯 Найдено {len(cards)} карточек с селектором '{selector}'")
                break
        
        if not cards:
            print(f"    ❌ Карточки не найдены")
            continue
            
        events_from_page = 0
        for card_idx, card in enumerate(cards[:10]):  # максимум 10 с одной страницы
            if events_from_page >= 3 or len(out) >= 5:
                break
                
            try:
                print(f"    🎫 Карточка {card_idx + 1}/{min(len(cards), 10)}")
                
                # Заголовок
                title_selectors = ["h1", "h2", "h3", "h4", ".title", ".headline", "[data-testid*='title']"]
                title = None
                for sel in title_selectors:
                    title_el = card.select_one(sel)
                    if title_el:
                        title = title_el.get_text(strip=True)
                        if title and len(title) >= 10:
                            break
                        title = None
                
                if not title:
                    print(f"      ❌ Заголовок не найден")
                    continue
                
                print(f"      📝 Заголовок: {title}")
                
                # Ссылка
                link_el = card.select_one("a")
                if not link_el:
                    print(f"      ❌ Ссылка не найдена")
                    continue
                    
                event_url = link_el.get("href", "")
                if not event_url:
                    print(f"      ❌ Пустая ссылка")
                    continue
                    
                if event_url.startswith("/"):
                    event_url = "https://www.timeout.com" + event_url
                elif not event_url.startswith("http"):
                    print(f"      ❌ Невалидная ссылка: {event_url}")
                    continue
                
                # Дата - ищем везде
                date_str = None
                date_selectors = [".date", ".time", "time", "[data-testid*='date']", "[data-testid*='time']"]
                
                for sel in date_selectors:
                    date_el = card.select_one(sel)
                    if date_el:
                        date_text = date_el.get_text(strip=True)
                        if date_text:
                            start_date, end_date = parse_date_range(date_text)
                            if start_date:
                                date_str = start_date
                                break
                
                # Если дата не найдена, используем сегодня + 1 день (для свежих подборок)
                if not date_str:
                    date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                
                # Проверяем свежесть события
                if not is_fresh_event(date_str):
                    print(f"      🗓️ Событие не свежее: {date_str}")
                    continue
                
                print(f"      📅 Дата: {date_str}")
                
                # Изображение
                image = None
                img_el = card.select_one("img")
                if img_el:
                    image = img_el.get("src") or img_el.get("data-src") or img_el.get("data-lazy-src")
                    if image and image.startswith("/"):
                        image = "https://media.timeout.com" + image
                
                # Описание
                desc_el = card.select_one("p, .description, .summary, .excerpt")
                desc = desc_el.get_text(strip=True)[:300] if desc_el else None
                
                # Категория
                category_hint = cat_id or "events"
                if "music" in url or "nightlife" in url:
                    category_hint = "live_music_gigs"
                elif "art" in url or "culture" in url:
                    category_hint = "art_galleries"
                elif "food" in url:
                    category_hint = "food"
                
                # Теги
                tags = ["TimeOut Picks", "Fresh"]
                
                event = normalize_event(
                    title=title,
                    date_iso=date_str,
                    url=event_url,
                    source="timeout.com/bangkok",
                    category_hint=category_hint,
                    desc=desc,
                    image=image,
                    venue="Bangkok",
                    tags=tags
                )
                
                out.append(event)
                events_from_page += 1
                print(f"      ✅ Добавлено событие!")
                
            except Exception as e:
                print(f"      ❌ Ошибка парсинга карточки: {e}")
                continue
        
        print(f"    📊 Найдено {events_from_page} событий на странице")
        
        # Задержка между страницами
        if url_idx < len(urls) - 1:
            fetcher.smart_delay()
    
    elapsed = time.time() - start_time
    print(f"\n🎉 Time Out фетчер завершен: {len(out)} свежих событий за {elapsed:.1f}с")
    
    return out[:5]
