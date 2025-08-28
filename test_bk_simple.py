#!/usr/bin/env python3
"""
Тест простого BK Magazine фетчера с базовыми заголовками
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from tools.fetchers.bk_magazine_simple import fetch

def test_bk_simple():
    print("🔥 Тестируем простой BK Magazine фетчер...")
    
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
                print(f"     Venue: {event.get('venue', 'No venue')}")
                print(f"     Price: {event.get('price', 'No price')}")
                print(f"     Tags: {event.get('tags', [])}")
                print()
        
        # Тест 2: Категория food
        print("\n🍕 Тест 2: Категория food")
        food_events = fetch("food")
        print(f"✅ Получено food событий: {len(food_events)}")
        
        if food_events:
            print("  Первые 2 события:")
            for i, event in enumerate(food_events[:2]):
                print(f"  {i+1}. {event.get('title', 'No title')} - {event.get('date', 'No date')}")
        
        # Тест 3: Категория nightlife
        print("\n🎵 Тест 3: Категория nightlife")
        nightlife_events = fetch("nightlife")
        print(f"✅ Получено nightlife событий: {len(nightlife_events)}")
        
        if nightlife_events:
            print("  Первые 2 события:")
            for i, event in enumerate(nightlife_events[:2]):
                print(f"  {i+1}. {event.get('title', 'No title')} - {event.get('date', 'No date')}")
        
        print(f"\n📊 Общий итог: {len(events)} общих + {len(food_events)} food + {len(nightlife_events)} nightlife событий")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bk_simple()
