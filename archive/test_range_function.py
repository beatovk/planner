#!/usr/bin/env python3
"""
Тест для функции within_next_7_days_range
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from tools.fetchers.base import within_next_7_days_range
from datetime import datetime, timezone

def test_range_function():
    print("🧪 Тест функции within_next_7_days_range...")
    
    # Текущая дата (22 августа 2025)
    today = datetime.now(timezone.utc).date()
    print(f"📅 Сегодня: {today}")
    
    # Тестовые случаи
    test_cases = [
        # (start_date, end_date, expected, description)
        ("2025-08-15", "2025-08-24", True, "Vernissage - пересекается с окном"),
        ("2025-08-14", "2025-09-14", True, "The Power of Small - пересекается с окном"),
        ("2025-08-30", "2025-10-12", False, "Polyculture - не пересекается"),
        ("2025-05-17", "2025-06-20", False, "Прошлое событие"),
        ("2025-09-01", "2025-09-30", False, "Будущее событие"),
        ("2025-08-22", "2025-08-22", True, "Событие на сегодня"),
        ("2025-08-29", "2025-08-29", True, "Событие на последний день окна"),
    ]
    
    for start_date, end_date, expected, description in test_cases:
        result = within_next_7_days_range(start_date, end_date)
        status = "✅" if result == expected else "❌"
        print(f"{status} {description}")
        print(f"     {start_date} - {end_date} → {result} (ожидалось {expected})")
        print()

if __name__ == "__main__":
    test_range_function()
