#!/usr/bin/env python3
"""
Тест для проверки новых расширенных полей событий
"""

import requests
import json

def test_extended_fields():
    print("🧪 Тестируем расширенные поля событий...")
    
    base_url = "http://localhost:8000"
    
    # Тест 1: Проверяем новые поля в Eventbrite
    print("\n🎯 Тест 1: Eventbrite с новыми полями")
    payload = {
        "city": "Bangkok",
        "selected_category_ids": ["workshops"],
        "use_live": True,
        "date": "2025-08-22"
    }
    
    try:
        response = requests.post(f"{base_url}/api/day-cards", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Получено событий: {data['debug']['live_count']}")
            
            # Анализируем новые поля
            events_with_price = [e for e in data['items'] if e.get('price_min') is not None]
            events_with_popularity = [e for e in data['items'] if e.get('popularity') is not None]
            events_with_rating = [e for e in data['items'] if e.get('rating') is not None]
            
            print(f"  💰 События с ценой: {len(events_with_price)}")
            print(f"  👥 События с популярностью: {len(events_with_popularity)}")
            print(f"  ⭐ События с рейтингом: {len(events_with_rating)}")
            
            # Показываем примеры
            if events_with_price:
                example = events_with_price[0]
                print(f"  📊 Пример события с ценой: {example['title']}")
                print(f"     Цена: {example['price_min']} THB")
            
        else:
            print(f"  ❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    
    # Тест 2: Проверяем комбинированные категории
    print("\n🎯 Тест 2: Комбинированные категории")
    payload["selected_category_ids"] = ["art_exhibits", "workshops"]
    
    try:
        response = requests.post(f"{base_url}/api/day-cards", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Получено событий: {data['debug']['live_count']}")
            
            # Анализируем источники
            sources = {}
            for event in data['items']:
                source = event['source']
                if source not in sources:
                    sources[source] = {'count': 0, 'with_price': 0, 'with_popularity': 0}
                sources[source]['count'] += 1
                if event.get('price_min') is not None:
                    sources[source]['with_price'] += 1
                if event.get('popularity') is not None:
                    sources[source]['with_popularity'] += 1
            
            print(f"  🌐 Анализ по источникам:")
            for source, stats in sources.items():
                print(f"     {source}: {stats['count']} событий, {stats['with_price']} с ценой, {stats['with_popularity']} с популярностью")
            
        else:
            print(f"  ❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    
    # Тест 3: Проверяем недельный просмотр
    print("\n🎯 Тест 3: Week View с новыми полями")
    week_payload = {
        "city": "Bangkok",
        "selected_category_ids": ["workshops"],
        "use_live": True,
        "mode": "week",
        "date": "2025-08-22"
    }
    
    try:
        response = requests.post(f"{base_url}/api/plan-cards", json=week_payload)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Получено событий: {data['debug']['live_count']}")
            
            # Проверяем, что новые поля передаются
            total_events = sum(len(day['items']) for day in data['days'])
            events_with_new_fields = 0
            
            for day in data['days']:
                for event in day['items']:
                    if any(event.get(field) is not None for field in ['popularity', 'price_min', 'rating']):
                        events_with_new_fields += 1
            
            print(f"  📊 Всего событий: {total_events}")
            print(f"  🆕 Событий с новыми полями: {events_with_new_fields}")
            
        else:
            print(f"  ❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")

if __name__ == "__main__":
    test_extended_fields()
