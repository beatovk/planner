import time
from typing import Dict, List, Optional
from collections import deque, defaultdict
import threading

class CacheMetrics:
    """
    Метрики производительности кэша для SLO алармов.
    Потокобезопасный, с rolling window для расчёта статистик.
    """
    
    def __init__(self, window_minutes: int = 15):
        self.window_minutes = window_minutes
        self.window_seconds = window_minutes * 60
        
        # Потокобезопасность
        self._lock = threading.Lock()
        
        # Rolling windows для метрик
        self._cache_read_times = deque()
        self._db_read_times = deque()
        self._cache_hits = deque()
        self._cache_misses = deque()
        
        # Счётчики для текущего окна
        self._current_hits = 0
        self._current_misses = 0
    
    def record_cache_read(self, duration_ms: float):
        """Записывает время чтения из кэша."""
        with self._lock:
            now = time.time()
            self._cache_read_times.append((now, duration_ms))
            self._cleanup_old_entries(now)
    
    def record_db_read(self, duration_ms: float):
        """Записывает время чтения из БД."""
        with self._lock:
            now = time.time()
            self._db_read_times.append((now, duration_ms))
            self._cleanup_old_entries(now)
    
    def record_cache_hit(self):
        """Записывает попадание в кэш."""
        with self._lock:
            now = time.time()
            self._cache_hits.append(now)
            self._current_hits += 1
            self._cleanup_old_entries(now)
    
    def record_cache_miss(self):
        """Записывает промах кэша."""
        with self._lock:
            now = time.time()
            self._cache_misses.append(now)
            self._current_misses += 1
            self._cleanup_old_entries(now)
    
    def _cleanup_old_entries(self, now: float):
        """Удаляет старые записи из rolling window."""
        cutoff = now - self.window_seconds
        
        # Очищаем cache_read_times
        while self._cache_read_times and self._cache_read_times[0][0] < cutoff:
            self._cache_read_times.popleft()
        
        # Очищаем db_read_times
        while self._db_read_times and self._db_read_times[0][0] < cutoff:
            self._db_read_times.popleft()
        
        # Очищаем cache_hits
        while self._cache_hits and self._cache_hits[0] < cutoff:
            self._cache_hits.popleft()
        
        # Очищаем cache_misses
        while self._cache_misses and self._cache_misses[0] < cutoff:
            self._cache_misses.popleft()
    
    def get_metrics(self) -> Dict[str, float]:
        """Возвращает текущие метрики для SLO алармов."""
        with self._lock:
            now = time.time()
            self._cleanup_old_entries(now)
            
            # Кэш read метрики
            cache_read_times = [t[1] for t in self._cache_read_times]
            cache_read_ms_p50 = self._percentile(cache_read_times, 50) if cache_read_times else 0
            cache_read_ms_p95 = self._percentile(cache_read_times, 95) if cache_read_times else 0
            cache_read_ms_p99 = self._percentile(cache_read_times, 99) if cache_read_times else 0
            
            # БД read метрики
            db_read_times = [t[1] for t in self._db_read_times]
            db_read_ms_p50 = self._percentile(db_read_times, 50) if db_read_times else 0
            db_read_ms_p95 = self._percentile(db_read_times, 95) if db_read_times else 0
            
            # Hit rate
            total_requests = len(self._cache_hits) + len(self._cache_misses)
            hit_rate = len(self._cache_hits) / total_requests if total_requests > 0 else 0
            miss_rate = 1 - hit_rate
            
            return {
                "cache_read_ms_p50": cache_read_ms_p50,
                "cache_read_ms_p95": cache_read_ms_p95,
                "cache_read_ms_p99": cache_read_ms_p99,
                "db_read_ms_p50": db_read_ms_p50,
                "db_read_ms_p95": db_read_ms_p95,
                "hit_rate": hit_rate,
                "miss_rate": miss_rate,
                "total_requests": total_requests,
                "window_minutes": self.window_minutes
            }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Вычисляет перцентиль для списка значений."""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def check_slo_alerts(self) -> List[Dict[str, str]]:
        """Проверяет SLO алармы и возвращает список нарушений."""
        metrics = self.get_metrics()
        alerts = []
        
        # Hit rate < 0.6 за 15 минут
        if metrics["hit_rate"] < 0.6 and metrics["total_requests"] >= 10:
            alerts.append({
                "type": "hit_rate_low",
                "severity": "warning",
                "message": f"Hit rate {metrics['hit_rate']:.2%} below SLO threshold 60%",
                "current": metrics["hit_rate"],
                "threshold": 0.6
            })
        
        # Cache read P95 > 120ms
        if metrics["cache_read_ms_p95"] > 120:
            alerts.append({
                "type": "cache_read_slow",
                "severity": "warning",
                "message": f"Cache read P95 {metrics['cache_read_ms_p95']:.1f}ms above SLO threshold 120ms",
                "current": metrics["cache_read_ms_p95"],
                "threshold": 120
            })
        
        # DB read P95 > 500ms
        if metrics["db_read_ms_p95"] > 500:
            alerts.append({
                "type": "db_read_slow",
                "severity": "critical",
                "message": f"DB read P95 {metrics['db_read_ms_p95']:.1f}ms above SLO threshold 500ms",
                "current": metrics["db_read_ms_p95"],
                "threshold": 500
            })
        
        return alerts

# Глобальный экземпляр метрик
metrics = CacheMetrics()
