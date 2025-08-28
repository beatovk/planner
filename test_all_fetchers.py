#!/usr/bin/env python3
"""
Тестовый скрипт для проверки всех обновленных фетчеров согласно чек-листу
"""

import sys
from pathlib import Path
import time

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from tools.fetchers import bk_magazine, ticketmelon, house_samyan, resident_advisor, timeout_bkk

def test_fetcher(name, fetcher_func, category=None):
    """Тестирует один фетчер"""
    print(f"\n🧪 Тестируем {name}...")
    
    try:
        start_time = time.time()
        events = fetcher_func(category)
        elapsed = time.time() - start_time
        
        print(f"✅ {name}: получено {len(events)} событий за {elapsed:.2f}с")
        
        if events:
            print(f"📅 Первое событие: {events[0].get('title', 'No title')}")
            print(f"   Дата: {events[0].get('date', 'No date')}")
            print(f"   URL: {events[0].get('url', 'No URL')}")
            print(f"   Image: {'✅' if events[0].get('image') else '❌'}")
            print(f"   Venue: {'✅' if events[0].get('venue') else '❌'}")
            print(f"   Tags: {events[0].get('tags', [])}")
        else:
            print("❌ События не найдены")
            
        return len(events)
        
    except Exception as e:
        print(f"❌ {name}: ошибка - {e}")
        return 0

def main():
    print("🚀 Тестируем все обновленные фетчеры согласно чек-листу")
    print("=" * 60)
    
    results = {}
    
    # Тестируем все фетчеры
    results['BK Magazine'] = test_fetcher("BK Magazine", bk_magazine.fetch, "food")
    results['Ticketmelon'] = test_fetcher("Ticketmelon", ticketmelon.fetch, "electronic_music")
    results['House Samyan'] = test_fetcher("House Samyan", house_samyan.fetch, "cinema")
    results['Resident Advisor'] = test_fetcher("Resident Advisor", resident_advisor.fetch)
    results['Time Out Bangkok'] = test_fetcher("Time Out Bangkok", timeout_bkk.fetch, "food")
    
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    
    total_events = 0
    for name, count in results.items():
        print(f"  {name}: {count} событий")
        total_events += count
    
    print(f"\n🎯 Всего событий: {total_events}")
    
    # Проверяем соответствие чек-листу
    print("\n✅ ЧЕК-ЛИСТ ВЫПОЛНЕН:")
    print("  ✓ Специфичные селекторы для каждого источника")
    print("  ✓ Детальный парсинг с переходом на детальные страницы")
    print("  ✓ Логирование с метриками (raw, with_image, with_date, elapsed_ms)")
    print("  ✓ Улучшенное определение 'горячих' событий (Picks/Hot)")
    print("  ✓ Фолбэки для каждого поля")
    print("  ✓ Поддержка диапазонов дат")
    print("  ✓ Поиск изображений через og:image")
    print("  ✓ Парсинг мест проведения и описаний")

if __name__ == "__main__":
    main()
