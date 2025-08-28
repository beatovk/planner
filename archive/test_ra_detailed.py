#!/usr/bin/env python3
"""
Детальный тест для Resident Advisor
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from tools.fetchers.base import get_html

def test_ra_detailed():
    print("🧪 Детальный тест Resident Advisor...")
    
    LIST_URL = "https://ra.co/events/thailand/bangkok"
    print(f"🌐 Проверяем: {LIST_URL}")
    
    # Получаем страницу
    soup = get_html(LIST_URL)
    if not soup:
        print("❌ Не удалось получить страницу")
        return
    
    print("✅ Страница получена")
    
    # Ищем все ссылки
    all_links = soup.find_all("a", href=True)
    print(f"📋 Всего ссылок: {len(all_links)}")
    
    # Ищем ссылки на события
    event_links = soup.select("li a[href^='/events/']")
    print(f"🎵 Ссылок на события: {len(event_links)}")
    
    if not event_links:
        print("❌ Ссылки на события не найдены")
        # Попробуем найти любые ссылки с /events/
        events_links = soup.find_all("a", href=lambda x: x and "/events/" in x)
        print(f"🔍 Ссылок с /events/: {len(events_links)}")
        
        if events_links:
            print("📋 Первые 5 ссылок с /events/:")
            for i, link in enumerate(events_links[:5]):
                href = link.get("href", "")
                text = link.get_text(strip=True)[:50]
                print(f"  {i+1}. {href} - {text}")
        return
    
    # Проверяем первые несколько ссылок
    print(f"\n🔍 Проверяем первые {min(3, len(event_links))} ссылки:")
    
    for i, link in enumerate(event_links[:3]):
        href = link.get("href", "")
        text = link.get_text(strip=True)
        print(f"\n  {i+1}. {text}")
        print(f"     Ссылка: {href}")
        
        # Ищем дату
        time_el = link.find_previous("time")
        if time_el:
            datetime_attr = time_el.get("datetime")
            time_text = time_el.get_text(strip=True)
            print(f"     📅 Time элемент: datetime='{datetime_attr}', text='{time_text}'")
        else:
            print("     ❌ Time элемент не найден")
            
            # Ищем дату в соседних элементах
            parent = link.parent
            if parent:
                time_siblings = parent.find_all("time")
                if time_siblings:
                    print(f"     📅 Найдено time элементов в родителе: {len(time_siblings)}")
                    for j, t in enumerate(time_siblings[:2]):
                        print(f"       {j+1}. datetime='{t.get('datetime')}', text='{t.get_text()}'")
                else:
                    print("     ❌ Time элементы в родителе не найдены")

if __name__ == "__main__":
    test_ra_detailed()
