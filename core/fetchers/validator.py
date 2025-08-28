from __future__ import annotations

from typing import Any, Iterable, List, Optional

from ..events import Event
from ..pydantic_compat import IS_PYDANTIC_V2
from ..logging import logger


def ensure_events(
    objs: Iterable[Any], *, source_name: Optional[str] = None, limit: Optional[int] = None
) -> List[Event]:
    """Validate and normalize raw objects into an ``Event`` list.

    Invalid entries are logged as warnings and skipped.
    """
    events: List[Event] = []
    total = 0
    bad = 0
    for obj in objs:
        total += 1
        try:
            if isinstance(obj, Event):
                event = obj
            elif IS_PYDANTIC_V2:
                event = Event.model_validate(obj)
            else:
                event = Event.parse_obj(obj)
            # Если у события пустой source — мягко подставим известное имя источника.
            if source_name and (not getattr(event, "source", None)):
                event.source = source_name  # type: ignore[attr-defined]
            events.append(event)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Invalid event from %s: %s", source_name or "unknown", exc)
            bad += 1
    if bad:
        logger.info(
            "ensure_events(%s): ok=%d bad=%d total=%d",
            source_name or "unknown", len(events), bad, total
        )
    # Применяем limit после валидации, чтобы не терять «счастливые» карточки при выбросе брака.
    return events[:limit] if isinstance(limit, int) and limit > 0 else events
