from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from ..models_places.place import Place


class FetcherPlaceInterface(ABC):
    """Base contract for place fetchers.

    Implementations return already normalised :class:`Place` objects.
    Exceptions from parsing individual places must be handled internally and
    must not leak to the caller.
    """

    # Человекопонятное имя источника для логов/метрик.
    name: str = "unknown"

    @abstractmethod
    def fetch(
        self, city: str, category: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Place]:
        """Retrieve places from the source.
        
        Args:
            city: City name (e.g., "bangkok")
            category: Optional category filter
            limit: Optional limit on number of places to return
            
        Returns:
            List of normalized Place objects
        """
        raise NotImplementedError

    def get_supported_cities(self) -> List[str]:
        """Return list of cities this fetcher supports."""
        return ["bangkok"]  # Default implementation

    def get_supported_categories(self) -> List[str]:
        """Return list of categories this fetcher supports."""
        return []  # Default implementation - no category filtering
