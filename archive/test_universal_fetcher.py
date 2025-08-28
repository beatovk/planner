#!/usr/bin/env python3
"""
Тест универсального фетчера - все источники по всем категориям
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from tools.fetchers.universal_fetcher import fetch_all_sources, fetch_by_category, fetch_all_categories

def test_universal_fetcher():
    print("🔥 Тестируем универсальный фетчер - все источники!")
    
    try:
        # Тест 1: Все источники без категории
        print("\n📋 Тест 1: Все источники (без категории)")
        all_events = fetch_all_sources()
        print(f"✅ Получено событий: {len(all_events)}")
        
        if all_events:
            print("\n📅 Первые 5 событий:")
            for i, event in enumerate(all_events[:5]):
                print(f"  {i+1}. {event.get('title', 'No title')}")
                print(f"     Дата: {event.get('date_iso', 'No date')}")
                print(f"     URL: {event.get('url', 'No URL')}")
                print(f"     Source: {event.get('source', 'No source')}")
                print(f"     Category: {event.get('category_hint', 'No category')}")
                print()
        
        # Тест 2: Категория food
        print("\n🍕 Тест 2: Категория food")
        food_events = fetch_by_category("food", max_events=20)
        print(f"✅ Получено food событий: {len(food_events)}")
        
        if food_events:
            print("  Первые 3 события:")
            for i, event in enumerate(food_events[:3]):
                print(f"  {i+1}. {event.get('title', 'No title')} - {event.get('source', 'No source')}")
        
        # Тест 3: Категория nightlife
        print("\n🎵 Тест 3: Категория nightlife")
        nightlife_events = fetch_by_category("live_music_gigs", max_events=20)
        print(f"✅ Получено nightlife событий: {len(nightlife_events)}")
        
        if nightlife_events:
            print("  Первые 3 события:")
            for i, event in enumerate(nightlife_events[:3]):
                print(f"  {i+1}. {event.get('title', 'No title')} - {event.get('source', 'No source')}")
        
        # Тест 4: Категория markets
        print("\n🛍️ Тест 4: Категория markets")
        markets_events = fetch_by_category("markets_fairs", max_events=20)
        print(f"✅ Получено markets событий: {len(markets_events)}")
        
        if markets_events:
            print("  Первые 3 события:")
            for i, event in enumerate(markets_events[:3]):
                print(f"  {i+1}. {event.get('title', 'No title')} - {event.get('source', 'No source')}")
        
        # Тест 5: Все категории (краткий)
        print("\n🎯 Тест 5: Все категории (краткий)")
        print("⚠️  Это займет время...")
        
        # Тестируем только 3 категории для экономии времени
        test_categories = {
            "food": "Еда и рестораны",
            "live_music_gigs": "Живая музыка", 
            "markets_fairs": "Рынки и ярмарки"
        }
        
        category_results = {}
        for cat_id, cat_name in test_categories.items():
            print(f"\n🎯 Категория: {cat_name} ({cat_id})")
            try:
                events = fetch_by_category(cat_id, max_events=15)
                category_results[cat_id] = events
                print(f"   📊 Получено {len(events)} событий")
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
                category_results[cat_id] = []
        
        # Итоги по категориям
        print(f"\n📊 Итоги по категориям:")
        total_events = 0
        for cat_id, events in category_results.items():
            print(f"  {cat_id}: {len(events)} событий")
            total_events += len(events)
        print(f"  Всего: {total_events} событий")
        
        # Общий итог
        print(f"\n📊 Общий итог: {len(all_events)} общих + {len(food_events)} food + {len(nightlife_events)} nightlife + {len(markets_events)} markets")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_universal_fetcher()
