#!/usr/bin/env python3
"""
Тест для анализа структуры Eventbrite
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from tools.fetchers.base import get_html
from urllib.parse import quote_plus

def test_eventbrite_structure():
    print("🧪 Анализ структуры Eventbrite...")
    
    SEARCH_BASE = "https://www.eventbrite.com/d/thailand--bangkok/{query}/"
    query = "workshops"
    url = SEARCH_BASE.format(query=quote_plus(query))
    
    print(f"🌐 Проверяем: {url}")
    
    soup = get_html(url)
    if not soup:
        print("❌ Не удалось получить страницу")
        return
    
    print("✅ Страница получена")
    
    # Ищем заголовки
    headers = soup.find_all(["h1", "h2", "h3", "h4"])
    print(f"📄 Заголовки: {len(headers)}")
    for header in headers[:5]:
        text = header.get_text(strip=True)
        if text:
            print(f"  {header.name}: {text}")
    
    # Ищем ссылки на события
    event_links = soup.find_all("a", href=lambda x: x and "/e/" in x)
    print(f"\n🔗 Ссылок на события (/e/): {len(event_links)}")
    
    if event_links:
        print("📋 Первые 5 ссылок на события:")
        for i, link in enumerate(event_links[:5]):
            href = link.get("href", "")
            text = link.get_text(strip=True)[:50]
            print(f"  {i+1}. {href} - {text}")
    
    # Ищем карточки по другим селекторам
    print(f"\n🔍 Поиск карточек по разным селекторам:")
    
    selectors = [
        "div[data-testid*='event']",
        "div[class*='event']",
        "div[class*='card']",
        "article",
        "div[class*='listing']"
    ]
    
    for selector in selectors:
        elements = soup.select(selector)
        print(f"  {selector}: {len(elements)} элементов")

if __name__ == "__main__":
    test_eventbrite_structure()
