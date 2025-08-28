"""
Performance metrics for the Week Planner system.
"""

import time
from typing import Dict, Any


class Metrics:
    """Performance metrics collector."""

    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_reads = []
        self.db_reads = []

    def record_cache_hit(self):
        """Record a cache hit."""
        self.cache_hits += 1

    def record_cache_miss(self):
        """Record a cache miss."""
        self.cache_misses += 1

    def record_cache_read(self, duration_ms: float):
        """Record cache read duration."""
        self.cache_reads.append(duration_ms)

    def record_db_read(self, duration_ms: float):
        """Record database read duration."""
        self.db_reads.append(duration_ms)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": (
                self.cache_hits / (self.cache_hits + self.cache_misses)
                if (self.cache_hits + self.cache_misses) > 0
                else 0
            ),
            "avg_cache_read_ms": (
                sum(self.cache_reads) / len(self.cache_reads) if self.cache_reads else 0
            ),
            "avg_db_read_ms": (
                sum(self.db_reads) / len(self.db_reads) if self.db_reads else 0
            ),
        }

    def check_slo_alerts(self) -> Dict[str, Any]:
        """Check SLO violations."""
        alerts = []

        # Check cache hit rate
        hit_rate = (
            self.cache_hits / (self.cache_hits + self.cache_misses)
            if (self.cache_hits + self.cache_misses) > 0
            else 0
        )
        if hit_rate < 0.8:
            alerts.append(f"Low cache hit rate: {hit_rate:.2%}")

        # Check response times
        if self.cache_reads and sum(self.cache_reads) / len(self.cache_reads) > 100:
            alerts.append("Slow cache reads detected")

        if self.db_reads and sum(self.db_reads) / len(self.db_reads) > 500:
            alerts.append("Slow database reads detected")

        return {"alerts": alerts}


# Global metrics instance
metrics = Metrics()
