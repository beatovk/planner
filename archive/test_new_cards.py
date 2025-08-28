#!/usr/bin/env python3
"""
Тест для проверки новых карточек с описаниями
"""

import requests
import json

def test_new_cards():
    print("🧪 Тестируем новые карточки с описаниями...")
    
    base_url = "http://localhost:8000"
    
    # Тест 1: Day View с одной категорией
    print("\n🎯 Тест 1: Day View (Art Exhibits)")
    payload = {
        "city": "Bangkok",
        "selected_category_ids": ["art_exhibits"],
        "use_live": True,
        "date": "2025-08-22"
    }
    
    try:
        response = requests.post(f"{base_url}/api/day-cards", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Получено событий: {data['debug']['live_count']}")
            print(f"  📅 Дата: {data['date']}")
            
            # Проверяем первое событие
            if data['items']:
                first_event = data['items'][0]
                print(f"  🎨 Первое событие: {first_event['title']}")
                print(f"  📝 Описание: {first_event.get('desc', 'Нет')[:50]}...")
                print(f"  🔗 Источник: {first_event['source']}")
        else:
            print(f"  ❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    
    # Тест 2: Day View с комбинированными категориями
    print("\n🎯 Тест 2: Day View (Art + Workshops)")
    payload["selected_category_ids"] = ["art_exhibits", "workshops"]
    
    try:
        response = requests.post(f"{base_url}/api/day-cards", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Получено событий: {data['debug']['live_count']}")
            
            # Проверяем разнообразие источников
            sources = set(item['source'] for item in data['items'])
            print(f"  🌐 Источники: {', '.join(sources)}")
        else:
            print(f"  ❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    
    # Тест 3: Week View
    print("\n🎯 Тест 3: Week View")
    week_payload = {
        "city": "Bangkok",
        "selected_category_ids": ["art_exhibits"],
        "use_live": True,
        "mode": "week",
        "date": "2025-08-22"
    }
    
    try:
        response = requests.post(f"{base_url}/api/plan-cards", json=week_payload)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Получено событий: {data['debug']['live_count']}")
            print(f"  📅 Период: {data['debug']['date_from']} → {data['debug']['date_to']}")
            print(f"  📊 Дней: {len(data['days'])}")
            
            # Проверяем первый день
            if data['days']:
                first_day = data['days'][0]
                print(f"  🌅 {first_day['day']}: {len(first_day['items'])} событий")
        else:
            print(f"  ❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")

if __name__ == "__main__":
    test_new_cards()
