from __future__ import annotations
from typing import Dict, List, Optional
import time
import re
import random
from datetime import datetime, timedelta
from .base import normalize_event, parse_date_range

ROOT = "https://bk.asia-city.com"

def get_bk_html(url: str, timeout: int = 15) -> Optional[BeautifulSoup]:
    """
    Простой HTTP-фетчер с базовыми заголовками для BK Magazine
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

def fetch(cat_id: str = None) -> List[Dict]:
    """
    Простой фетчер для BK Magazine по схеме Time Out
    """
    start_time = time.time()
    out = []
    
    # URL для парсинга - реальные рабочие страницы
    urls = [
        f"{ROOT}/things-to-do-bangkok/news",  # Новости событий
        f"{ROOT}/restaurants/news",           # Новости ресторанов
        f"{ROOT}/nightlife/news",             # Новости ночной жизни
        f"{ROOT}/travel/news"                 # Новости путешествий
    ]
    
    print(f"🚀 Запускаем простой BK Magazine фетчер...")
    
    for i, url in enumerate(urls):
        if len(out) >= 20:  # лимит на фетчер
            break
            
        print(f"\n📋 Страница {i+1}/{len(urls)}: {url}")
        
        soup = get_bk_html(url)
        if not soup:
            continue
            
        # Ищем карточки событий для Drupal 7
        selectors = [
            ".node",                      # Drupal узлы
            "article",                    # Статьи
            ".view-content .views-row",   # Drupal Views ряды
            ".content",                   # Контент
            ".main-content",              # Основной контент
            ".region-content",            # Регион контента
            ".field-content",             # Поля контента
            ".post",                      # Посты
            ".event",                     # События
            ".listing",                   # Списки
            ".card",                      # Карточки
            ".item"                       # Элементы
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
            if len(out) >= 20:
                break
                
            try:
                print(f"    🎫 Карточка {j+1}/{min(len(cards), 8)}")
                
                # Заголовок для Drupal 7
                title_selectors = [
                    "h1", "h2", "h3", "h4",           # Заголовки
                    ".node__title a",                  # Drupal заголовки узлов
                    ".title", ".post-title",           # Заголовки постов
                    ".field--name-title",              # Drupal поля заголовков
                    ".headline", ".entry-title",       # Заголовки статей
                    "a[href*='/']"                     # Ссылки
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
                    "a[href*='/']",                    # Ссылки на события
                    "a",                               # Fallback на любую ссылку
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
                    event_url = ROOT + event_url
                elif not event_url.startswith("http"):
                    continue
                
                # Описание
                desc_selectors = [
                    "p",                               # Параграфы
                    ".summary", ".excerpt",            # Суммарии
                    ".description", ".content"         # Описания
                ]
                
                desc = None
                for sel in desc_selectors:
                    desc_el = card.select_one(sel)
                    if desc_el:
                        desc = desc_el.get_text(strip=True)[:300]
                        break
                
                # Изображение
                image_selectors = [
                    "img[src*='bk.asia-city.com']",   # Изображения BK
                    "img"                             # Fallback на любое изображение
                ]
                
                image = None
                for sel in image_selectors:
                    img_el = card.select_one(sel)
                    if img_el:
                        image = img_el.get("src") or img_el.get("data-src") or img_el.get("data-lazy-src")
                        if image and image.startswith("/"):
                            image = ROOT + image
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
                tags = ["BK Magazine"]
                
                # Нормализуем событие
                event = normalize_event(
                    title=title,
                    url=event_url,
                    desc=desc,
                    image=image,
                    date_iso=date_str,  # Исправлено: date -> date_iso
                    venue=venue,
                    price_min=price,
                    source="BK Magazine",  # Добавлен обязательный параметр
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
    print(f"\n🎉 BK Magazine фетчер завершен: {len(out)} свежих событий за {elapsed:.1f}с")
    
    return out
