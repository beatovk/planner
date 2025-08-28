#!/usr/bin/env python3
"""
Тест для проверки всего процесса получения событий
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from core.live_events import load_source_map, fetch_for_categories

def test_full_process():
    print("🧪 Тест полного процесса получения событий...")
    
    # Шаг 1: Загружаем карту источников
    print("📋 Шаг 1: Загружаем карту источников...")
    sources_path = Path("data/sources.json")
    source_map = load_source_map(sources_path)
    print(f"  Источники загружены: {list(source_map.keys())}")
    
    # Шаг 2: Проверяем категорию art_exhibits
    print(f"\n🎨 Шаг 2: Проверяем категорию 'art_exhibits'...")
    if "art_exhibits" in source_map:
        sources = source_map["art_exhibits"]
        print(f"  Источники для art_exhibits: {sources}")
    else:
        print("  ❌ Категория 'art_exhibits' не найдена в карте источников")
        return
    
    # Шаг 3: Получаем события
    print(f"\n📅 Шаг 3: Получаем события...")
    try:
        events = fetch_for_categories(source_map, ["art_exhibits"])
        print(f"  Событий получено: {len(events)}")
        
        if events:
            print(f"  Первые 3 события:")
            for i, event in enumerate(events[:3]):
                title = event.get('title', 'No title')
                date = event.get('date', 'No date')
                end = event.get('end', 'No end')
                print(f"    {i+1}. {title}")
                print(f"       Период: {date} - {end}")
        else:
            print("  ❌ События не найдены")
            
    except Exception as e:
        print(f"  ❌ Ошибка при получении событий: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_process()
