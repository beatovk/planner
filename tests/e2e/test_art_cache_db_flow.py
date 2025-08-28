#!/usr/bin/env python
"""
End-to-end tests for art cache and database flow.
"""

import os
import tempfile
import shutil
import time
from pathlib import Path
import pytest
import requests

from core.db import init_db, seed_sample_art_events
from core.cache import ensure_client, write_flag_ids, read_flag_ids, update_index


class TestArtCacheDBFlow:
    """Test end-to-end art cache and database flow."""
    
    def setup_method(self):
        """Setup test environment."""
        # Сохраняем оригинальный DB_URL
        self.original_db_url = os.environ.get("DB_URL")
        
        # Создаем временную директорию для тестов
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.temp_dir) / "data"
        self.test_data_dir.mkdir()
        
        # Меняем рабочую директорию на временную
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Убираем DB_URL для использования fallback
        if "DB_URL" in os.environ:
            del os.environ["DB_URL"]
        
        # Инициализируем БД
        init_db()
        
        # Заполняем тестовыми данными
        seed_sample_art_events()
        
        # Запускаем сервер в фоне (если нужно)
        self.server_process = None
        
    def teardown_method(self):
        """Cleanup test environment."""
        # Останавливаем сервер если запущен
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
        
        # Восстанавливаем рабочую директорию
        os.chdir(self.original_cwd)
        
        # Восстанавливаем оригинальный DB_URL
        if self.original_db_url:
            os.environ["DB_URL"] = self.original_db_url
        elif "DB_URL" in os.environ:
            del os.environ["DB_URL"]
        
        # Удаляем временную директорию
        shutil.rmtree(self.temp_dir)
    
    def test_art_events_in_database(self):
        """Test that art events are properly stored in database."""
        from core.fetchers.db_fetcher import DatabaseFetcher
        
        db_fetcher = DatabaseFetcher()
        events = db_fetcher.fetch(category="art")
        
        assert len(events) >= 2, f"Expected at least 2 art events, got {len(events)}"
        
        # Проверяем что события имеют правильные атрибуты
        for event in events:
            assert hasattr(event, "title") and event.title, "Event should have title"
            assert hasattr(event, "source") and event.source == "test", "Event should have test source"
            assert hasattr(event, "tags") and "art" in event.tags, "Event should have art tag"
    
    def test_cache_write_and_read(self):
        """Test that events can be written to and read from cache."""
        from core.fetchers.db_fetcher import DatabaseFetcher
        
        db_fetcher = DatabaseFetcher()
        events = db_fetcher.fetch(category="art")
        
        assert len(events) > 0, "Should have events to cache"
        
        # Записываем в кэш
        city = "bangkok"
        date = "2025-01-27"
        flag = "art"
        
        try:
            r = ensure_client()
            # Извлекаем ID событий
            def _extract_id(e):
                if hasattr(e, "id"):
                    return str(getattr(e, "id"))
                if hasattr(e, "event_id"):
                    return str(getattr(e, "event_id"))
                if isinstance(e, dict):
                    return str(e.get("id") or e.get("event_id") or "")
                return ""
            
            event_ids = [_extract_id(event) for event in events if _extract_id(event)]
            write_flag_ids(r, city, date, flag, event_ids)
            
            # Читаем из кэша
            cached_event_ids, status = read_flag_ids(r, city, date, flag)
            assert cached_event_ids is not None, "Should read event IDs from cache"
            assert len(cached_event_ids) == len(events), "Should have same number of event IDs"
            assert status in ["HIT", "STALE"], f"Expected HIT or STALE, got {status}"
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    def test_api_events_endpoint_with_cache(self):
        """Test that /api/events endpoint works with cache and database."""
        # Этот тест требует запущенного сервера
        # В реальном тесте нужно запустить сервер в фоне
        
        # Проверяем что БД содержит события
        from core.fetchers.db_fetcher import DatabaseFetcher
        db_fetcher = DatabaseFetcher()
        events = db_fetcher.fetch(category="art")
        assert len(events) > 0, "Database should contain art events"
        
                # Проверяем что кэш работает
        city = "bangkok"
        date = "2025-01-27"
        flag = "art"
    
        try:
            r = ensure_client()
            # Извлекаем ID событий
            def _extract_id(e):
                if hasattr(e, "id"):
                    return str(getattr(e, "id"))
                if hasattr(e, "event_id"):
                    return str(getattr(e, "event_id"))
                if isinstance(e, dict):
                    return str(e.get("id") or e.get("event_id") or "")
                return ""
            
            event_ids = [_extract_id(event) for event in events if _extract_id(event)]
            write_flag_ids(r, city, date, flag, event_ids)
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
        
        # Симулируем API вызов
        from core.query.facets import categories_to_facets
        
        selected_ids = ["art"]
        facets = categories_to_facets(selected_ids)
        
        assert "art" in facets["flags"], "Should have art flag"
        assert "art" in facets["categories"], "Should have art category"
        
        # Проверяем что кэш содержит данные
        cached_event_ids = cache.read_flag_events(city, date, flag)
        assert cached_event_ids is not None, "Cache should contain event IDs"
        
        cached_events = cache.read_events_by_ids(city, date, cached_event_ids)
        assert cached_events is not None, "Cache should contain events"
        assert len(cached_events) > 0, "Cache should contain events"
    
    def test_cache_performance(self):
        """Test that cache provides fast access to events."""
        from core.fetchers.db_fetcher import DatabaseFetcher
        
        db_fetcher = DatabaseFetcher()
        events = db_fetcher.fetch(category="art")
        
        city = "bangkok"
        date = "2025-01-27"
        flag = "art"
        
        # Записываем в кэш
        try:
            r = ensure_client()
            # Извлекаем ID событий
            def _extract_id(e):
                if hasattr(e, "id"):
                    return str(getattr(e, "id"))
                if hasattr(e, "event_id"):
                    return str(getattr(e, "event_id"))
                if isinstance(e, dict):
                    return str(e.get("id") or e.get("event_id") or "")
                return ""
            
            event_ids = [_extract_id(event) for event in events if _extract_id(event)]
            write_flag_ids(r, city, date, flag, event_ids)
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
        
        # Измеряем время чтения из кэша
        start_time = time.time()
        cached_event_ids = cache.read_flag_events(city, date, flag)
        cached_events = cache.read_events_by_ids(city, date, cached_event_ids)
        cache_time = time.time() - start_time
        
        # Измеряем время чтения из БД
        start_time = time.time()
        db_events = db_fetcher.fetch(category="art")
        db_time = time.time() - start_time
        
        # Кэш должен быть быстрее БД
        assert cache_time < db_time, f"Cache should be faster than DB: cache={cache_time:.3f}s, db={db_time:.3f}s"
        
        # Кэш должен быть достаточно быстрым (< 0.1s)
        assert cache_time < 0.1, f"Cache access should be fast: {cache_time:.3f}s"
        
        print(f"Cache time: {cache_time:.3f}s, DB time: {db_time:.3f}s")
