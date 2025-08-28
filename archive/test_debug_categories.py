#!/usr/bin/env python3
"""
Диагностический тест для проверки категорий live_music_gigs и markets_fairs
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from tools.fetchers.universal_fetcher import fetch_by_category

def test_debug_categories():
    print("🔍 Диагностический тест для проблемных категорий...")
    
    try:
        # Тест 1: live_music_gigs
        print("\n🎵 Тест 1: live_music_gigs")
        print("=" * 50)
        live_music_events = fetch_by_category("live_music_gigs", max_events=50)
        print(f"✅ Получено live_music_gigs событий: {len(live_music_events)}")
        
        if live_music_events:
            print("\n📅 События live_music_gigs:")
            for i, event in enumerate(live_music_events[:3]):
                print(f"  {i+1}. {event.get('title', 'No title')}")
                print(f"     Source: {event.get('source', 'No source')}")
                print(f"     URL: {event.get('url', 'No URL')}")
                print()
        
        # Тест 2: markets_fairs
        print("\n🛍️ Тест 2: markets_fairs")
        print("=" * 50)
        markets_events = fetch_by_category("markets_fairs", max_events=50)
        print(f"✅ Получено markets_fairs событий: {len(markets_events)}")
        
        if markets_events:
            print("\n📅 События markets_fairs:")
            for i, event in enumerate(markets_events[:3]):
                print(f"  {i+1}. {event.get('title', 'No title')}")
                print(f"     Source: {event.get('source', 'No source')}")
                print(f"     URL: {event.get('url', 'No URL')}")
                print()
        
        # Тест 3: food (для сравнения)
        print("\n🍕 Тест 3: food (для сравнения)")
        print("=" * 50)
        food_events = fetch_by_category("food", max_events=50)
        print(f"✅ Получено food событий: {len(food_events)}")
        
        if food_events:
            print("\n📅 События food:")
            for i, event in enumerate(food_events[:3]):
                print(f"  {i+1}. {event.get('title', 'No title')}")
                print(f"     Source: {event.get('source', 'No source')}")
                print(f"     URL: {event.get('url', 'No URL')}")
                print()
        
        print(f"\n📊 Итоги:")
        print(f"  live_music_gigs: {len(live_music_events)} событий")
        print(f"  markets_fairs: {len(markets_events)} событий")
        print(f"  food: {len(food_events)} событий")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_debug_categories()
