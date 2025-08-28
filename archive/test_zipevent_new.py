#!/usr/bin/env python3
"""
Тестовый скрипт для нового Zipevent фетчера на основе sitemap
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from tools.fetchers.zipevent import fetch

def test_zipevent_new():
    print("🧪 Тестируем новый Zipevent фетчер (sitemap подход)...")
    
    try:
        # Тестируем без категории (все события)
        print("\n📋 Тест 1: Все события")
        events = fetch()
        print(f"✅ Получено событий: {len(events)}")
        
        if events:
            print("\n📅 Первые 3 события:")
            for i, event in enumerate(events[:3]):
                print(f"  {i+1}. {event.get('title', 'No title')}")
                print(f"     Дата: {event.get('date', 'No date')} - {event.get('end', 'No end')}")
                print(f"     URL: {event.get('url', 'No URL')}")
                print(f"     Venue: {event.get('venue', 'No venue')}")
                print(f"     Image: {event.get('image', 'No image')}")
                print(f"     Tags: {event.get('tags', [])}")
                print(f"     Category: {event.get('category_hint', 'No category')}")
                print()
        
        # Тестируем с категорией food
        print("\n🍕 Тест 2: Категория food")
        food_events = fetch("food")
        print(f"✅ Получено food событий: {len(food_events)}")
        
        if food_events:
            print("\n📅 Food события:")
            for i, event in enumerate(food_events[:2]):
                print(f"  {i+1}. {event.get('title', 'No title')}")
                print(f"     Дата: {event.get('date', 'No date')}")
                print(f"     Category: {event.get('category_hint', 'No category')}")
                print()
        
        # Тестируем с категорией markets_fairs
        print("\n🛍️ Тест 3: Категория markets_fairs")
        market_events = fetch("markets_fairs")
        print(f"✅ Получено market событий: {len(market_events)}")
        
        if market_events:
            print("\n📅 Market события:")
            for i, event in enumerate(market_events[:2]):
                print(f"  {i+1}. {event.get('title', 'No title')}")
                print(f"     Дата: {event.get('date', 'No date')}")
                print(f"     Category: {event.get('category_hint', 'No category')}")
                print()
        
        # Статистика по категориям
        print("\n📊 Статистика по категориям:")
        category_stats = {}
        for event in events:
            cat = event.get('category_hint', 'unknown')
            category_stats[cat] = category_stats.get(cat, 0) + 1
        
        for cat, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {count} событий")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_zipevent_new()
