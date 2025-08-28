from __future__ import annotations
import logging

# Либ-код не трогает глобальную конфигурацию логов.
# Добавляем NullHandler, чтобы пользователь сам решал, куда писать.
logger = logging.getLogger("fetcher")
if not logger.handlers:
    logger.addHandler(logging.NullHandler())

__all__ = ["logger"]
