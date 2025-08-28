import time
from core.metrics import CacheMetrics

def test_metrics_initialization():
    """Тест инициализации метрик."""
    metrics = CacheMetrics(window_minutes=5)
    assert metrics.window_minutes == 5
    assert metrics.window_seconds == 300

def test_record_cache_hit():
    """Тест записи попадания в кэш."""
    metrics = CacheMetrics(window_minutes=5)
    metrics.record_cache_hit()
    metrics.record_cache_hit()
    
    result = metrics.get_metrics()
    assert result["hit_rate"] == 1.0
    assert result["miss_rate"] == 0.0
    assert result["total_requests"] == 2

def test_record_cache_miss():
    """Тест записи промаха кэша."""
    metrics = CacheMetrics(window_minutes=5)
    metrics.record_cache_miss()
    metrics.record_cache_miss()
    
    result = metrics.get_metrics()
    assert result["hit_rate"] == 0.0
    assert result["miss_rate"] == 1.0
    assert result["total_requests"] == 2

def test_mixed_hits_and_misses():
    """Тест смешанных попаданий и промахов."""
    metrics = CacheMetrics(window_minutes=5)
    metrics.record_cache_hit()
    metrics.record_cache_miss()
    metrics.record_cache_hit()
    
    result = metrics.get_metrics()
    assert abs(result["hit_rate"] - 2/3) < 0.001
    assert abs(result["miss_rate"] - 1/3) < 0.001
    assert result["total_requests"] == 3

def test_timing_metrics():
    """Тест метрик времени."""
    metrics = CacheMetrics(window_minutes=5)
    metrics.record_cache_read(100.0)  # 100ms
    metrics.record_cache_read(200.0)  # 200ms
    metrics.record_db_read(50.0)      # 50ms
    
    result = metrics.get_metrics()
    assert abs(result["cache_read_ms_p50"] - 150.0) < 0.1
    # P95 для 2 значений [100, 200]: 95% от 1 = 0.95, что даёт 100 + 0.95*100 = 195
    assert abs(result["cache_read_ms_p95"] - 195.0) < 0.1
    assert abs(result["db_read_ms_p50"] - 50.0) < 0.1

def test_slo_alerts():
    """Тест SLO алармов."""
    metrics = CacheMetrics(window_minutes=5)
    
    # Добавляем медленные запросы для триггера аларма
    for _ in range(10):
        metrics.record_cache_read(150.0)  # Выше порога 120ms
    
    alerts = metrics.check_slo_alerts()
    assert len(alerts) > 0
    
    # Проверяем что есть аларм о медленном кэше
    cache_slow_alerts = [a for a in alerts if a["type"] == "cache_read_slow"]
    assert len(cache_slow_alerts) > 0
    assert cache_slow_alerts[0]["severity"] == "warning"

def test_window_cleanup():
    """Тест очистки старых записей."""
    metrics = CacheMetrics(window_minutes=1)  # Короткое окно для теста
    
    # Записываем метрики
    metrics.record_cache_hit()
    metrics.record_cache_read(100.0)
    
    # Проверяем что записи есть
    result = metrics.get_metrics()
    assert result["total_requests"] == 1
    
    # Симулируем старое время (больше чем window_minutes)
    old_time = time.time() + 300  # +5 минут
    
    # Принудительно вызываем очистку с будущим временем
    metrics._cleanup_old_entries(old_time)
    
    result = metrics.get_metrics()
    assert result["total_requests"] == 0

def test_cleanup_old_entries():
    """Тест очистки старых записей без ожидания."""
    metrics = CacheMetrics(window_minutes=5)
    
    # Записываем метрики
    metrics.record_cache_hit()
    metrics.record_cache_read(100.0)
    
    # Проверяем что записи есть
    result = metrics.get_metrics()
    assert result["total_requests"] == 1
    
    # Симулируем старое время (больше чем window_minutes)
    old_time = time.time() + 300  # +5 минут
    
    # Принудительно вызываем очистку с будущим временем
    metrics._cleanup_old_entries(old_time)
    
    result = metrics.get_metrics()
    assert result["total_requests"] == 0

def test_global_metrics_instance():
    """Тест что глобальный экземпляр метрик работает."""
    from core.metrics import metrics as global_metrics
    
    # Очищаем глобальные метрики для чистого теста
    global_metrics._cache_hits.clear()
    global_metrics._cache_misses.clear()
    global_metrics._cache_read_times.clear()
    global_metrics._db_read_times.clear()
    
    # Записываем тестовые данные
    global_metrics.record_cache_hit()
    global_metrics.record_cache_read(100.0)
    
    result = global_metrics.get_metrics()
    assert result["total_requests"] == 1
    assert result["hit_rate"] == 1.0
