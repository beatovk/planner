from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from ..events import Event


class FetcherInterface(ABC):
    """Base contract for event fetchers.

    Implementations return already normalised :class:`Event` objects.
    Exceptions from parsing individual cards must be handled internally and
    must not leak to the caller.
    """

    # Человекопонятное имя источника для логов/метрик.
    name: str = "unknown"

    @abstractmethod
    def fetch(
        self, category: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Event]:
        """Retrieve events from the source."""
        raise NotImplementedError
