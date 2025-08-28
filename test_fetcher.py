#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы фетчера Bangkok Art City
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from tools.fetchers.bangkok_art_city import fetch

def test_bangkok_art_city():
    print("🧪 Тестируем Bangkok Art City фетчер...")
    
    try:
        events = fetch()
        print(f"✅ Получено событий: {len(events)}")
        
        if events:
            print("\n📅 Первые события:")
            for i, event in enumerate(events[:3]):
                print(f"  {i+1}. {event.get('title', 'No title')}")
                print(f"     Дата: {event.get('date', 'No date')} - {event.get('end', 'No end')}")
                print(f"     URL: {event.get('url', 'No URL')}")
                print()
        else:
            print("❌ События не найдены")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bangkok_art_city()
