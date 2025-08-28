#!/usr/bin/env python3
"""
Тестовый скрипт для проверки базовых утилит фетчера
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from tools.fetchers.base import get_html, parse_date_range

def test_base_utilities():
    print("🧪 Тестируем базовые утилиты...")
    
    # Тест 1: Парсинг диапазонов дат
    print("\n📅 Тест парсинга диапазонов дат:")
    test_cases = [
        "6 Sep — 7 Dec 2025",
        "22 Aug - 30 Sep 2025", 
        "13—25 Aug 2025",
        "15 September 2025",
        "Invalid date"
    ]
    
    for test_case in test_cases:
        result = parse_date_range(test_case)
        print(f"  '{test_case}' → {result}")
    
    # Тест 2: Получение HTML (проверим доступность сайта)
    print("\n🌐 Тест доступности Bangkok Art City:")
    try:
        soup = get_html("https://www.bangkokartcity.org")
        if soup:
            print("  ✅ Сайт доступен")
            # Попробуем найти заголовок
            title = soup.find("title")
            if title:
                print(f"  📄 Заголовок: {title.get_text()[:100]}...")
            else:
                print("  ❌ Заголовок не найден")
        else:
            print("  ❌ Сайт недоступен")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")

if __name__ == "__main__":
    test_base_utilities()
