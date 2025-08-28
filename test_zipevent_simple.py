#!/usr/bin/env python3
"""
Простейший тест для диагностики Zipevent
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from tools.fetchers.zipevent import get_event_urls_from_sitemap, parse_event_page

def test_simple():
    print("🔍 Диагностический тест Zipevent...")
    
    # Тест 1: получаем первые 3 URL из sitemap
    print("\n1️⃣ Тест sitemap...")
    urls = get_event_urls_from_sitemap()
    if urls:
        print(f"✅ Sitemap работает: {len(urls)} событий")
        
        # Ищем свежие события 2024-2025
        print(f"🔍 Ищем свежие события 2024-2025...")
        fresh_urls = []
        for url in urls:  # проверяем весь sitemap
            if "2024" in url or "2025" in url:
                fresh_urls.append(url)
                if len(fresh_urls) >= 3:
                    break
        
        print(f"🔍 Проверено URL: {len(urls)}")
        print(f"🔍 Найдено свежих: {len(fresh_urls)}")
        
        # Показываем первые 10 URL для отладки
        print(f"🔍 Первые 10 URL:")
        for i, url in enumerate(urls[:10]):
            print(f"  {i+1}. {url}")
        
        if fresh_urls:
            print(f"✅ Найдено {len(fresh_urls)} свежих событий:")
            for url in fresh_urls:
                print(f"  - {url}")
            test_urls = fresh_urls
        else:
            print("❌ Свежих событий не найдено, используем первые 3")
            test_urls = urls[:3]
            for url in test_urls:
                print(f"  - {url}")
    else:
        print("❌ Sitemap не работает")
        return
    
    # Тест 2: парсим одно событие
    print("\n2️⃣ Тест парсинга события...")
    test_url = test_urls[0]
    event = parse_event_page(test_url)
    if event:
        print(f"✅ Событие распарсилось:")
        print(f"  Title: {event.get('title')}")
        print(f"  Date: {event.get('date_iso')}")
        print(f"  URL: {event.get('url')}")
        print(f"  Desc: {event.get('desc', '')[:100]}...")
    else:
        print(f"❌ Событие не распарсилось: {test_url}")

if __name__ == "__main__":
    test_simple()
