import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from packages.wp_cache.cache import CacheClient, get_cache_client
from packages.wp_places.service import PlacesService
from packages.wp_places.dao import init_schema, save_places
from packages.wp_core.db import get_engine
from packages.wp_core.config import get_cache_key, get_cache_ttl, is_cache_enabled


@pytest.fixture
def temp_db():
    """Создание временной БД для тестов"""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    db_url = f"sqlite:///{db_path}"
    engine = get_engine(db_url)

    yield engine

    engine.dispose()
    os.unlink(db_path)


@pytest.fixture
def sample_places():
    """Тестовые данные мест"""
    return [
        {
            "id": "test_place_1",
            "name": "Test Place 1",
            "description": "Test description 1",
            "city": "bangkok",
            "address": "Test Address 1",
            "tags": ["test", "place"],
            "flags": ["test_flag"],
            "typical_time": "day",
            "source": "test",
            "rating": 4.5,
            "price_range": "$$",
            "google_maps_url": "https://maps.google.com/test1",
        },
        {
            "id": "test_place_2",
            "name": "Test Place 2",
            "description": "Test description 2",
            "city": "bangkok",
            "address": "Test Address 2",
            "tags": ["test", "place"],
            "flags": ["test_flag"],
            "typical_time": "evening",
            "source": "test",
            "rating": 4.0,
            "price_range": "$",
            "google_maps_url": "https://maps.google.com/test2",
        },
    ]


@pytest.fixture
def mock_redis_client():
    """Mock Redis client для тестов"""
    mock_client = Mock()
    mock_client.get.return_value = None
    mock_client.setex.return_value = True
    mock_client.exists.return_value = False
    mock_client.ttl.return_value = -1
    mock_client.keys.return_value = []
    mock_client.delete.return_value = 1
    mock_client.info.return_value = {
        "redis_version": "6.0.0",
        "connected_clients": 1,
        "used_memory_human": "1M",
        "total_commands_processed": 100,
    }
    return mock_client


@pytest.fixture
def cache_client(mock_redis_client):
    """Cache client с mock Redis"""
    with patch(
        "packages.wp_cache.cache.get_sync_client", return_value=mock_redis_client
    ):
        with patch("packages.wp_cache.cache.should_bypass_redis", return_value=False):
            return get_cache_client()


class TestCacheClient:
    """Тесты для CacheClient"""

    def test_init_with_redis(self, mock_redis_client):
        """Тест инициализации с Redis"""
        with patch(
            "packages.wp_cache.cache.get_sync_client", return_value=mock_redis_client
        ):
            with patch(
                "packages.wp_cache.cache.should_bypass_redis", return_value=False
            ):
                client = CacheClient()
                assert client._redis_client is not None
                assert not client._cache_bypass

    def test_init_without_redis(self):
        """Тест инициализации без Redis"""
        with patch(
            "packages.wp_cache.cache.get_sync_client",
            side_effect=Exception("Redis unavailable"),
        ):
            with patch(
                "packages.wp_cache.cache.should_bypass_redis", return_value=False
            ):
                client = CacheClient()
                assert client._redis_client is None
                assert client._cache_bypass

    def test_get_json_cache_hit(self, cache_client, mock_redis_client):
        """Тест получения JSON из кэша (hit)"""
        # Подготавливаем mock для возврата данных
        mock_redis_client.get.return_value = b'{"test": "data"}'

        result = cache_client.get_json("test_key")

        assert result == {"test": "data"}
        mock_redis_client.get.assert_called_once_with("test_key")

    def test_get_json_cache_miss(self, cache_client, mock_redis_client):
        """Тест получения JSON из кэша (miss)"""
        # Mock возвращает None (кэш miss)
        mock_redis_client.get.return_value = None

        result = cache_client.get_json("test_key")

        assert result is None
        mock_redis_client.get.assert_called_once_with("test_key")

    def test_set_json_success(self, cache_client, mock_redis_client):
        """Тест сохранения JSON в кэш (успех)"""
        test_data = {"test": "data"}

        result = cache_client.set_json("test_key", test_data, ttl=1800)

        assert result is True
        # Проверяем, что setex был вызван с правильными параметрами
        mock_redis_client.setex.assert_called_once()
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][0] == "test_key"  # key
        assert call_args[0][1] == 1800  # ttl
        # value должен быть JSON строка
        assert '"test"' in call_args[0][2]

    def test_set_json_failure(self, cache_client, mock_redis_client):
        """Тест сохранения JSON в кэш (неудача)"""
        # Mock возвращает False при setex
        mock_redis_client.setex.return_value = False

        result = cache_client.set_json("test_key", {"test": "data"})

        assert result is False

    def test_with_fallback_cache_hit(self, cache_client, mock_redis_client):
        """Тест with_fallback с кэш hit"""
        # Подготавливаем mock для возврата данных из кэша
        mock_redis_client.get.return_value = b'{"cached": "data"}'

        def producer():
            return {"produced": "data"}

        result = cache_client.with_fallback("test_key", producer)

        assert result == {"cached": "data"}
        # producer не должен вызываться
        mock_redis_client.get.assert_called_once()

    def test_with_fallback_cache_miss(self, cache_client, mock_redis_client):
        """Тест with_fallback с кэш miss"""
        # Mock возвращает None (кэш miss)
        mock_redis_client.get.return_value = None

        def producer():
            return {"produced": "data"}

        result = cache_client.with_fallback("test_key", producer)

        assert result == {"produced": "data"}
        # Должен быть вызов get и setex
        assert mock_redis_client.get.call_count == 1
        assert mock_redis_client.setex.call_count == 1

    def test_delete_success(self, cache_client, mock_redis_client):
        """Тест удаления ключа из кэша"""
        result = cache_client.delete("test_key")

        assert result is True
        mock_redis_client.delete.assert_called_once_with("test_key")

    def test_exists_true(self, cache_client, mock_redis_client):
        """Тест проверки существования ключа (существует)"""
        mock_redis_client.exists.return_value = True

        result = cache_client.exists("test_key")

        assert result is True
        mock_redis_client.exists.assert_called_once_with("test_key")

    def test_exists_false(self, cache_client, mock_redis_client):
        """Тест проверки существования ключа (не существует)"""
        mock_redis_client.exists.return_value = False

        result = cache_client.exists("test_key")

        assert result is False

    def test_get_ttl_valid(self, cache_client, mock_redis_client):
        """Тест получения TTL ключа (валидный)"""
        mock_redis_client.ttl.return_value = 1800

        result = cache_client.get_ttl("test_key")

        assert result == 1800
        mock_redis_client.ttl.assert_called_once_with("test_key")

    def test_get_ttl_expired(self, cache_client, mock_redis_client):
        """Тест получения TTL ключа (истекший)"""
        mock_redis_client.ttl.return_value = -1

        result = cache_client.get_ttl("test_key")

        assert result is None

    def test_get_stats(self, cache_client, mock_redis_client):
        """Тест получения статистики кэша"""
        stats = cache_client.get_stats()

        assert "cache_enabled" in stats
        assert "redis_status" in stats
        assert "default_ttl" in stats
        assert "timestamp" in stats
        assert stats["cache_enabled"] is True


class TestPlacesServiceCache:
    """Тесты кэширования в PlacesService"""

    def test_cache_key_generation(self):
        """Тест генерации стандартизированных ключей кэша"""
        # Ключ для флага
        flag_key = get_cache_key("bangkok", "food_dining")
        assert flag_key == "v2:places:bangkok:flag:food_dining"

        # Ключ для поиска
        search_key = get_cache_key("bangkok", query="jazz", limit=20)
        assert search_key == "v2:places:bangkok:search:jazz:20"

        # Ключ для всех мест
        all_key = get_cache_key("bangkok")
        assert all_key == "v2:places:bangkok:all"

    def test_cache_ttl_configuration(self):
        """Тест конфигурации TTL кэша"""
        default_ttl = get_cache_ttl("default")
        long_ttl = get_cache_ttl("long")
        short_ttl = get_cache_ttl("short")

        assert default_ttl > 0
        assert long_ttl > default_ttl
        assert short_ttl < default_ttl

    @patch("packages.wp_core.config.CACHE_BYPASS", True)
    def test_cache_bypass_enabled(self):
        """Тест отключения кэша через CACHE_BYPASS"""
        assert is_cache_enabled() is False

    @patch("packages.wp_core.config.CACHE_BYPASS", False)
    def test_cache_bypass_disabled(self):
        """Тест включения кэша через CACHE_BYPASS"""
        assert is_cache_enabled() is True


class TestCacheIntegration:
    """Интеграционные тесты кэширования"""

    def test_places_service_cache_integration(self, temp_db, sample_places):
        """Тест интеграции кэширования в PlacesService"""
        # Инициализируем БД
        init_schema(temp_db)
        save_places(temp_db, sample_places)

        # Создаем PlacesService с mock кэшем
        with patch("packages.wp_places.service.get_cache_client") as mock_get_cache:
            mock_cache = Mock()
            mock_cache.get_json.return_value = None  # Кэш miss
            mock_cache.set_json.return_value = True
            mock_get_cache.return_value = mock_cache

            service = PlacesService()

            # Выполняем поиск
            places = service.search_places("test", limit=10)

            # Проверяем, что кэш был использован
            assert mock_cache.get_json.called
            assert mock_cache.set_json.called

    def test_cache_pattern_clearing(self, cache_client, mock_redis_client):
        """Тест очистки кэша по паттерну"""
        # Mock возвращает ключи для паттерна
        mock_redis_client.keys.return_value = [
            "v2:places:bangkok:flag:food",
            "v2:places:bangkok:flag:drinks",
        ]

        result = cache_client.clear_pattern("v2:places:bangkok:*")

        assert result == 2
        mock_redis_client.keys.assert_called_once_with("v2:places:bangkok:*")
        mock_redis_client.delete.assert_called_once_with(
            "v2:places:bangkok:flag:food", "v2:places:bangkok:flag:drinks"
        )
