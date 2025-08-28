#!/usr/bin/env python3
"""
Тест для проверки фильтрации событий по датам
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from tools.fetchers.bangkok_art_city import fetch
from tools.fetchers.base import within_next_7_days
from datetime import datetime, timezone

def test_filtering():
    print("🧪 Тест фильтрации событий по датам...")
    
    # Получаем все события
    all_events = fetch()
    print(f"📅 Всего событий: {len(all_events)}")
    
    if not all_events:
        print("❌ События не найдены")
        return
    
    # Показываем первые 5 событий с датами
    print(f"\n📋 Первые 5 событий:")
    for i, event in enumerate(all_events[:5]):
        date = event.get('date', 'No date')
        end = event.get('end', 'No end')
        title = event.get('title', 'No title')
        print(f"  {i+1}. {title}")
        print(f"     Период: {date} - {end}")
    
    # Проверяем, сколько событий попадает в окно ближайших 7 дней
    print(f"\n🔍 Фильтрация по окну ближайших 7 дней:")
    
    today = datetime.now(timezone.utc).date()
    end_date = today + timedelta(days=7)
    print(f"  Окно: {today} - {end_date}")
    
    filtered_events = []
    for event in all_events:
        date = event.get('date')
        if date and within_next_7_days(date):
            filtered_events.append(event)
    
    print(f"  Событий в окне: {len(filtered_events)}")
    
    if filtered_events:
        print(f"  Примеры событий в окне:")
        for i, event in enumerate(filtered_events[:3]):
            title = event.get('title', 'No title')
            date = event.get('date', 'No date')
            print(f"    {i+1}. {title} - {date}")
    else:
        print(f"  ❌ Нет событий в ближайшие 7 дней")
        print(f"  💡 Возможно, все события в будущем или прошлом")
        
        # Проверим диапазон дат
        dates = [event.get('date') for event in all_events if event.get('date')]
        if dates:
            min_date = min(dates)
            max_date = max(dates)
            print(f"  📊 Диапазон дат в данных: {min_date} - {max_date}")

if __name__ == "__main__":
    from datetime import timedelta
    test_filtering()
