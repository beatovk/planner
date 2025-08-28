import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from core.cache import ensure_client, write_flag_ids, update_index, is_configured
from core.fetchers.db_fetcher import DatabaseFetcher

log = logging.getLogger("prewarm")

class CachePrewarmer:
    """
    Планировщик прогрева кэша для топ-флагов.
    Запускается ночью и прогревает кэш на 7-14 дней вперёд.
    """
    
    def __init__(self):
        self.top_flags = ["art", "market", "music", "culture", "food"]
        self.days_ahead = 14
        self.city = "bangkok"
    
    async def prewarm_top_flags(self):
        """Основной метод прогрева топ-флагов."""
        if not is_configured():
            log.warning("Redis not configured, skipping prewarm")
            return
        
        log.info("Starting cache prewarm for top flags: %s", self.top_flags)
        
        try:
            redis_client = ensure_client()
            db_fetcher = DatabaseFetcher()
            
            # Прогреваем на следующие 14 дней
            today = datetime.now().date()
            for day_offset in range(1, self.days_ahead + 1):
                target_date = today + timedelta(days=day_offset)
                date_str = target_date.isoformat()
                
                log.info("Prewarming date: %s", date_str)
                
                for flag in self.top_flags:
                    try:
                        # Пытаемся получить события для этого флага и даты
                        events = db_fetcher.fetch(category=flag)
                        
                        if events:
                            # Извлекаем ID событий
                            event_ids = []
                            for event in events:
                                if hasattr(event, "id"):
                                    event_ids.append(str(getattr(event, "id")))
                                elif isinstance(event, dict) and event.get("id"):
                                    event_ids.append(str(event["id"]))
                            
                            if event_ids:
                                # Записываем в кэш
                                write_flag_ids(redis_client, self.city, date_str, flag, event_ids)
                                log.info("Prewarmed %s:%s:%s with %d events", 
                                       self.city, date_str, flag, len(event_ids))
                            else:
                                log.warning("No event IDs found for %s:%s:%s", 
                                          self.city, date_str, flag)
                        else:
                            log.debug("No events found for %s:%s:%s", 
                                    self.city, date_str, flag)
                    
                    except Exception as e:
                        log.error("Failed to prewarm %s:%s:%s: %s", 
                                self.city, date_str, flag, str(e))
                
                # Обновляем индекс дня
                try:
                    flag_counts = {}
                    for flag in self.top_flags:
                        # Проверяем что записалось
                        from core.cache import read_flag_ids
                        ids, _ = read_flag_ids(redis_client, self.city, date_str, flag)
                        if ids:
                            flag_counts[flag] = len(ids)
                    
                    if flag_counts:
                        update_index(redis_client, self.city, date_str, flag_counts=flag_counts)
                        log.info("Updated index for %s:%s with flags: %s", 
                               self.city, date_str, flag_counts)
                
                except Exception as e:
                    log.error("Failed to update index for %s:%s: %s", 
                            self.city, date_str, str(e))
                
                # Небольшая пауза между днями
                await asyncio.sleep(0.1)
        
        except Exception as e:
            log.error("Cache prewarm failed: %s", str(e))
        
        log.info("Cache prewarm completed")

async def run_prewarm():
    """Запускает процесс прогрева кэша."""
    prewarmer = CachePrewarmer()
    await prewarmer.prewarm_top_flags()

def schedule_prewarm():
    """Планирует ночной прогрев кэша."""
    import schedule
    import time
    
    def job():
        log.info("Running scheduled cache prewarm")
        asyncio.run(run_prewarm())
    
    # Запускаем в 2:00 ночи каждый день
    schedule.every().day.at("02:00").do(job)
    
    log.info("Scheduled cache prewarm for 02:00 daily")
    
    # Запускаем планировщик
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверяем каждую минуту

if __name__ == "__main__":
    # Для тестирования можно запустить сразу
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_prewarm())
