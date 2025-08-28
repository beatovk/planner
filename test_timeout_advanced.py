#!/usr/bin/env python3
"""
Тест продвинутого Time Out Bangkok фетчера с bypass методами
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from tools.fetchers.timeout_bkk_advanced import fetch

def test_timeout_advanced():
    print("🔥 Тестируем продвинутый Time Out Bangkok фетчер...")
    
    try:
        # Тест 1: Все события
        print("\n📋 Тест 1: Все события")
        events = fetch()
        print(f"✅ Получено событий: {len(events)}")
        
        if events:
            print("\n📅 События:")
            for i, event in enumerate(events):
                print(f"  {i+1}. {event.get('title', 'No title')}")
                print(f"     Дата: {event.get('date', 'No date')}")
                print(f"     URL: {event.get('url', 'No URL')}")
                print(f"     Category: {event.get('category_hint', 'No category')}")
                print(f"     Tags: {event.get('tags', [])}")
                print()
        
        # Тест 2: Категория food
        print("\n🍕 Тест 2: Категория food")
        food_events = fetch("food")
        print(f"✅ Получено food событий: {len(food_events)}")
        
        if food_events:
            for i, event in enumerate(food_events[:2]):
                print(f"  {i+1}. {event.get('title', 'No title')} - {event.get('date', 'No date')}")
        
        # Тест 3: Музыка
        print("\n🎵 Тест 3: Категория music")
        music_events = fetch("live_music_gigs")
        print(f"✅ Получено music событий: {len(music_events)}")
        
        if music_events:
            for i, event in enumerate(music_events[:2]):
                print(f"  {i+1}. {event.get('title', 'No title')} - {event.get('date', 'No date')}")
                
        print(f"\n📊 Общий итог: {len(events)} общих + {len(food_events)} food + {len(music_events)} music событий")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_timeout_advanced()
