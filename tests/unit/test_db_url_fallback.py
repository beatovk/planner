#!/usr/bin/env python
"""
Unit tests for database URL fallback functionality.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest

from core.db import get_db_url, get_engine, healthcheck, init_db


class TestDatabaseURLFallback:
    """Test database URL fallback functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        # Сохраняем оригинальный DB_URL
        self.original_db_url = os.environ.get("DB_URL")
        # Создаем временную директорию для тестов
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.temp_dir) / "data"
        self.test_data_dir.mkdir()
        
    def teardown_method(self):
        """Cleanup test environment."""
        # Восстанавливаем оригинальный DB_URL
        if self.original_db_url:
            os.environ["DB_URL"] = self.original_db_url
        elif "DB_URL" in os.environ:
            del os.environ["DB_URL"]
        
        # Удаляем временную директорию
        shutil.rmtree(self.temp_dir)
    
    def test_get_db_url_fallback(self):
        """Test that get_db_url returns fallback when DB_URL is not set."""
        # Убираем DB_URL из окружения
        if "DB_URL" in os.environ:
            del os.environ["DB_URL"]
        
        # Меняем рабочую директорию на временную
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            db_url = get_db_url()
            assert db_url.startswith("sqlite:///")
            assert "events.db" in db_url
            assert self.test_data_dir.exists()
        finally:
            os.chdir(original_cwd)
    
    def test_get_db_url_from_env(self):
        """Test that get_db_url uses DB_URL from environment."""
        test_db_url = "sqlite:///test.db"
        os.environ["DB_URL"] = test_db_url
        
        db_url = get_db_url()
        assert db_url == test_db_url
    
    def test_get_engine_with_fallback(self):
        """Test that get_engine works with fallback URL."""
        # Убираем DB_URL из окружения
        if "DB_URL" in os.environ:
            del os.environ["DB_URL"]
        
        # Меняем рабочую директорию на временную
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            engine = get_engine()
            assert engine is not None
            assert str(engine.url).startswith("sqlite:///")
        finally:
            os.chdir(original_cwd)
    
    def test_healthcheck_with_fallback(self):
        """Test that healthcheck works with fallback database."""
        # Убираем DB_URL из окружения
        if "DB_URL" in os.environ:
            del os.environ["DB_URL"]
        
        # Меняем рабочую директорию на временную
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            # Инициализируем БД
            init_db()
            
            # Проверяем healthcheck
            result = healthcheck()
            assert result is True
        finally:
            os.chdir(original_cwd)
    
    def test_init_db_creates_tables(self):
        """Test that init_db creates necessary tables."""
        # Убираем DB_URL из окружения
        if "DB_URL" in os.environ:
            del os.environ["DB_URL"]
        
        # Меняем рабочую директорию на временную
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            # Инициализируем БД
            result = init_db()
            assert result is True
            
            # Проверяем что файл БД создался
            db_file = self.test_data_dir / "events.db"
            assert db_file.exists()
        finally:
            os.chdir(original_cwd)
