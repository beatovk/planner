#!/usr/bin/env python3
"""
Week Planner - Ingestion с прогревом кэша по новым флагам.

Интегрируется с существующей системой кэширования и использует новый facets mapper
для автоматического определения флагов событий.
"""

import os
import sys
import argparse
import datetime as dt
import logging
from typing import List, Dict, Any

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger("ingest")

# Импорты из существующей системы
try:
    from core.cache import ensure_client, write_flag_ids, update_index
    from core.query.facets import map_event_to_flags
    from core.utils.dates import normalize_bkk_day
except ImportError as e:
    log.error("Failed to import core modules: %s", e)
    log.error("Make sure you're running from the project root")
    exit(1)

# Новые флаги для прогрева
DEFAULT_FLAGS = [
    "electronic_music",
    "live_music", 
    "jazz_blues",
    "rooftop",
    "food_dining",
    "art_exhibits",
    "workshops",
    "cinema",
    "markets",
    "yoga_wellness",
    "parks",
]

def daterange(start: dt.date, days: int):
    """Генератор дат от start на days вперёд."""
    for i in range(days):
        yield start + dt.timedelta(days=i)

def get_events_for_day(city: str, day: dt.date) -> List[Dict[str, Any]]:
    """
    Получает события для конкретного дня из БД.
    Использует существующий DatabaseFetcher или простой SQLite.
    """
    try:
        # Пробуем использовать существующий DatabaseFetcher
        from core.fetchers.database import DatabaseFetcher
        
        fetcher = DatabaseFetcher()
        events = fetcher.fetch_events_for_day(city, day.isoformat())
        return events
    except Exception as e:
        log.warning("DatabaseFetcher failed, trying direct SQLite: %s", e)
        
        # Fallback: прямой SQLite
        import sqlite3
        db_path = "data/wp.db"
        if not os.path.exists(db_path):
            log.warning("Database not found at %s", db_path)
            return []
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Простой запрос по датам - ищем события которые "затрагивают" день
        # Событие затрагивает день если start <= day <= end
        day_str = day.isoformat()
        
        cursor.execute("""
            SELECT id, title, desc, tags, source, city, start, end
            FROM events 
            WHERE city LIKE ? AND start <= ? AND end >= ?
        """, (f"%{city}%", day_str, day_str))
        
        rows = cursor.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            events.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "tags": row[3],
                "source": row[4],
                "city": row[5],
                "start": row[6],
                "end": row[7]
            })
        
        return events

def warmup_cache_for_day(city: str, day: dt.date, flags: List[str]) -> Dict[str, int]:
    """
    Прогревает кэш для конкретного дня и флагов.
    Возвращает статистику по каждому флагу.
    """
    log.info("Warming up cache for %s on %s", city, day.isoformat())
    
    # Получаем события для дня
    events = get_events_for_day(city, day)
    log.info("Found %d events for %s", len(events), day.isoformat())
    
    # Группируем события по флагам
    flag_counts: Dict[str, int] = {}
    flag_events: Dict[str, List[str]] = {}
    
    for flag in flags:
        flag_events[flag] = []
        flag_counts[flag] = 0
    
    # Маппим события на флаги
    for event in events:
        event_flags = map_event_to_flags(event)
        event_id = str(event.get("id", ""))
        
        for flag in event_flags:
            if flag in flag_events:
                flag_events[flag].append(event_id)
                flag_counts[flag] += 1
    
    # Записываем в кэш
    try:
        r = ensure_client()
        
        # Записываем флаги
        for flag in flags:
            if flag_events[flag]:
                write_flag_ids(r, city, day.isoformat(), flag, flag_events[flag])
                log.info("Wrote %d events for flag %s", len(flag_events[flag]), flag)
            else:
                # Пустой кэш для флага без событий
                write_flag_ids(r, city, day.isoformat(), flag, [])
                log.debug("Wrote empty cache for flag %s", flag)
        
        # Обновляем индекс дня
        update_index(r, city, day.isoformat(), flag_counts=flag_counts)
        log.info("Updated index for %s: %s", day.isoformat(), flag_counts)
        
    except Exception as e:
        log.error("Failed to warm up cache for %s: %s", day.isoformat(), e)
        return {}
    
    return flag_counts

def warmup_cache(city: str, dates: List[dt.date], flags: List[str]) -> Dict[str, Dict[str, int]]:
    """
    Прогревает кэш для диапазона дат и флагов.
    Возвращает статистику по дням и флагам.
    """
    log.info("Starting cache warmup for %s: %d dates, %d flags", city, len(dates), len(flags))
    
    results: Dict[str, Dict[str, int]] = {}
    
    for day in dates:
        try:
            day_stats = warmup_cache_for_day(city, day, flags)
            results[day.isoformat()] = day_stats
        except Exception as e:
            log.error("Failed to warm up cache for %s: %s", day.isoformat(), e)
            results[day.isoformat()] = {}
    
    return results

def main():
    """Основная функция CLI."""
    ap = argparse.ArgumentParser(description="Week Planner - Ingestion с прогревом кэша")
    ap.add_argument("--start-date", help="YYYY-MM-DD; default=today", default=None)
    ap.add_argument("--days-ahead", type=int, default=14, help="Количество дней вперёд")
    ap.add_argument("--days-back", type=int, default=0, help="Количество дней назад")
    ap.add_argument("--city", default="bangkok", help="Город для обработки")
    ap.add_argument("--flags", default="", help="Флаги для прогрева (через запятую)")
    ap.add_argument("--dry-run", action="store_true", help="Показать план без выполнения")
    args = ap.parse_args()

    # Проверяем переменные окружения
    if not os.environ.get("REDIS_URL"):
        log.error("REDIS_URL не задан")
        exit(1)
    
    if not os.environ.get("DB_URL") and not os.path.exists("data/wp.db"):
        log.error("DB_URL не задан и data/wp.db не найден")
        exit(1)

    # Определяем даты
    today = dt.date.today()
    start = dt.date.fromisoformat(args.start_date) if args.start_date else today
    start = start - dt.timedelta(days=args.days_back)
    
    # Генерируем диапазон дат
    total_days = args.days_back + args.days_ahead + 1
    dates = list(daterange(start, total_days))
    
    # Определяем флаги
    if args.flags:
        flags = [s.strip() for s in args.flags.split(",") if s.strip()]
    else:
        flags = DEFAULT_FLAGS
    
    log.info("=== План прогрева кэша ===")
    log.info("Город: %s", args.city)
    log.info("Диапазон: %s → %s (%d дней)", start.isoformat(), dates[-1].isoformat(), len(dates))
    log.info("Флаги: %s", ", ".join(flags))
    
    if args.dry_run:
        log.info("DRY RUN - показан план без выполнения")
        return
    
    # Выполняем прогрев
    try:
        results = warmup_cache(args.city, dates, flags)
        
        # Выводим статистику
        log.info("=== Результаты прогрева ===")
        total_events = 0
        for day, day_stats in results.items():
            day_total = sum(day_stats.values())
            total_events += day_total
            log.info("%s: %d событий (%s)", day, day_total, day_stats)
        
        log.info("Итого: %d событий обработано", total_events)
        
    except Exception as e:
        log.error("Ошибка при прогреве кэша: %s", e)
        exit(1)

if __name__ == "__main__":
    main()
