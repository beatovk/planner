from __future__ import annotations
from typing import Dict, List, Optional
import time
import re
import random
from datetime import datetime, timedelta
from .base import normalize_event, parse_date_range

ROOT = "https://www.timeout.com/bangkok"

def get_timeout_html(url: str, timeout: int = 15) -> Optional[BeautifulSoup]:
    """
    Простой HTTP-фетчер с базовыми заголовками
    """
    from bs4 import BeautifulSoup
    import requests
    
    # Простые заголовки
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        # Простой запрос без сессии
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code != 200:
            print(f"      ❌ HTTP {r.status_code} для {url}")
            return None
        
        print(f"      📊 {url}: HTTP {r.status_code} ({len(r.text)} символов)")
        return BeautifulSoup(r.text, "lxml")
        
    except Exception as e:
        print(f"      ❌ Ошибка получения {url}: {e}")
        return None

def is_fresh_event(date_str: str) -> bool:
    """Проверяет что событие в ближайшие 2 недели"""
    if not date_str:
        return False
        
    try:
        event_date = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.now()
        two_weeks_later = today + timedelta(weeks=2)
        
        return today <= event_date <= two_weeks_later
    except:
        return False

def fetch(cat_id: str = None, max_events: int = 50) -> List[Dict]:
    """
    Простой фетчер для Time Out Bangkok с поддержкой категорий
    """
    start_time = time.time()
    out = []
    
    # URL для парсинга в зависимости от категории
    if cat_id in ["food", "markets_fairs"]:
        urls = [
            f"{ROOT}/food-drink",
            f"{ROOT}/bars-pubs",
            f"{ROOT}/things-to-do"
        ]
    elif cat_id in ["live_music_gigs", "jazz_blues", "rooftops_bars"]:
        urls = [
            f"{ROOT}/music-nightlife",
            f"{ROOT}/bars-pubs",
            f"{ROOT}/things-to-do"
        ]
    elif cat_id in ["workshops", "parks_walks", "art_culture"]:
        urls = [
            f"{ROOT}/things-to-do",
            f"{ROOT}/art",
            f"{ROOT}/city-guide"
        ]
    elif cat_id in ["shopping", "wellness"]:
        urls = [
            f"{ROOT}/shopping",
            f"{ROOT}/things-to-do",
            f"{ROOT}/city-guide"
        ]
    else:
        # По умолчанию - все разделы
        urls = [
            f"{ROOT}/things-to-do",
            f"{ROOT}/food-drink",
            f"{ROOT}/bars-pubs",
            f"{ROOT}/news"
        ]
    
    print(f"🚀 Запускаем простой Time Out Bangkok фетчер для категории: {cat_id or 'all'}")
    
    for i, url in enumerate(urls):
        if len(out) >= max_events:  # настраиваемый лимит
            break
            
        print(f"\n📋 Страница {i+1}/{len(urls)}: {url}")
        
        soup = get_timeout_html(url)
        if not soup:
            continue
            
        # Ищем карточки событий
        selectors = [
            "article.tile._article_wkzyo_1", # Основные карточки событий с CSS модулями
            "article.tile",                  # Fallback на article.tile
            "article",                       # Fallback на article
            ".tile",                         # Fallback на .tile
            ".card", 
            ".listing",
            ".item",
            ".article-card",
            ".content-card",
            "[data-testid*='card']",
            ".package-card"
        ]
        
        cards = []
        for sel in selectors:
            cards = soup.select(sel)
            if cards:
                print(f"    🎯 Найдено {len(cards)} карточек с '{sel}'")
                break
        
        if not cards:
            print(f"    ❌ Карточки не найдены")
            continue
        
        # Парсим карточки
        for j, card in enumerate(cards[:8]):  # максимум 8 карточек с одной страницы
            if len(out) >= max_events:
                break
                
            try:
                print(f"    🎫 Карточка {j+1}/{min(len(cards), 8)}")
                
                # Заголовок
                title_selectors = [
                    "h3._h3_c6c0h_1",                    # Основной заголовок карточки
                    "[data-testid='tile-title_testID']",  # Test ID заголовка
                    "h1", "h2", "h3", "h4",              # Fallback на заголовки
                    ".title", ".headline", 
                    "[data-testid*='title']"
                ]
                
                title = None
                for sel in title_selectors:
                    title_el = card.select_one(sel)
                    if title_el:
                        title = title_el.get_text(strip=True)
                        if title and len(title) > 5:
                            break
                
                if not title:
                    print(f"      ❌ Заголовок не найден")
                    continue
                
                print(f"      📝 Заголовок: {title}")
                
                # Ссылка
                link_selectors = [
                    "a._titleLinkContainer_wkzyo_81",     # Контейнер ссылки заголовка
                    "a._imageLinkContainer_wkzyo_20",     # Контейнер ссылки изображения
                    "a[data-testid='tile-link_testID']",  # Test ID ссылки
                    "a[href*='/bangkok/']",               # Ссылки на события Бангкока
                    "a"                                   # Fallback на любую ссылку
                ]
                
                link_el = None
                for sel in link_selectors:
                    link_el = card.select_one(sel)
                    if link_el:
                        break
                
                if not link_el:
                    print(f"      ❌ Ссылка не найдена")
                    continue
                
                event_url = link_el.get("href", "")
                if not event_url:
                    print(f"      ❌ URL не найден")
                    continue
                    
                if event_url.startswith("/"):
                    event_url = "https://www.timeout.com" + event_url
                elif not event_url.startswith("http"):
                    continue
                
                # Описание
                desc_selectors = [
                    ".summary._summary_wkzyo_138 ._p_1mmxl_1", # Основное описание
                    "[data-testid='summary_testID']",           # Test ID описания
                    ".summary", ".excerpt",                     # Fallback
                    "p", ".description"
                ]
                
                desc = None
                for sel in desc_selectors:
                    desc_el = card.select_one(sel)
                    if desc_el:
                        desc = desc_el.get_text(strip=True)[:300]
                        break
                
                # Изображение
                image_selectors = [
                    "img._image_wkzyo_20",                    # Основное изображение карточки
                    "img[data-testid='responsive-image_testID']", # Test ID изображения
                    "img[src*='media.timeout.com']",           # Изображения Time Out
                    "img"                                     # Fallback на любое изображение
                ]
                
                image = None
                for sel in image_selectors:
                    img_el = card.select_one(sel)
                    if img_el:
                        image = img_el.get("src") or img_el.get("data-src") or img_el.get("data-lazy-src")
                        if image and image.startswith("/"):
                            image = "https://media.timeout.com" + image
                        break
                
                # Дата - ищем в тексте карточки
                card_text = card.get_text()
                date_patterns = [
                    r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b',
                    r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b',
                    r'\b\d{4}-\d{2}-\d{2}\b',
                    r'\b(?:Today|Tomorrow|This weekend|Next week)\b'
                ]
                
                date_str = None
                for pattern in date_patterns:
                    match = re.search(pattern, card_text, re.IGNORECASE)
                    if match:
                        date_str = match.group()
                        break
                
                if date_str:
                    print(f"      📅 Дата: {date_str}")
                else:
                    print(f"      ❌ Дата не найдена")
                    # Используем текущую дату как fallback
                    date_str = datetime.now().strftime("%Y-%m-%d")
                
                # Место/цена - ищем в тексте
                venue = "Bangkok"  # По умолчанию
                price = None
                
                # Категория
                category_hint = cat_id if cat_id else "general"
                
                # Теги
                tags = ["TimeOut"]
                
                # Нормализуем событие
                event = normalize_event(
                    title=title,
                    url=event_url,
                    desc=desc,
                    image=image,
                    date_iso=date_str,
                    venue=venue,
                    price_min=price,
                    source="Time Out Bangkok",  # Добавлен обязательный параметр
                    category_hint=category_hint,
                    tags=tags
                )
                
                if event:
                    out.append(event)
                    print(f"      ✅ Добавлено событие!")
                else:
                    print(f"      ❌ Событие не нормализовано")
                    
            except Exception as e:
                print(f"      ❌ Ошибка парсинга карточки: {e}")
                continue
        
        print(f"    📊 Найдено {len(out)} событий на странице")
        
        # Задержка между страницами
        if i < len(urls) - 1:
            delay = random.uniform(3, 6)
            print(f"    ⏱️ Задержка {delay:.1f}с...")
            time.sleep(delay)
    
    elapsed = time.time() - start_time
    print(f"\n🎉 Time Out фетчер завершен: {len(out)} свежих событий за {elapsed:.1f}с")
    
    return out
