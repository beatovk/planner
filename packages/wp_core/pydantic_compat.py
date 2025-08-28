"""
Small compatibility layer between Pydantic v1 and v2.
Provides unified helpers so code can be version agnostic.
"""

from __future__ import annotations

import pydantic
from typing import Any, Callable

IS_PYDANTIC_V2 = int(pydantic.__version__.split(".")[0]) >= 2

if IS_PYDANTIC_V2:
    from pydantic import (
        AnyUrl,
        BaseModel,
        ConfigDict,
        Field,
        field_validator,
        model_validator,
    )
else:
    from pydantic import AnyUrl, BaseModel, Field, root_validator, validator

    ConfigDict = dict

    def field_validator(*fields: str, mode: str = "after", **kwargs: Any) -> Callable:
        pre = mode == "before"
        return validator(*fields, pre=pre, **kwargs)

    def model_validator(mode: str = "after") -> Callable:
        """
        В v1 у нас нет @model_validator; эмулируем через root_validator.
        Для mode="after" даём fn(cls, obj) семантику: собираем obj обычным путём,
        затем преобразуем значения и возвращаем dict.
        """

        def decorator(fn: Callable) -> Callable:
            if mode == "before":
                # fn ожидает (cls, values)->values
                def wrapper_before(cls, values):
                    return fn(cls, values)

                return root_validator(pre=True)(wrapper_before)
            else:
                # fn ожидает (cls, obj)->obj
                def wrapper_after(cls, values):
                    # на этом этапе values — уже провалидированные поля
                    # создаём временный объект для совместимости с сигнатурой
                    obj = cls(**values)
                    new_obj = fn(cls, obj)
                    # вернуть словарь полей
                    return (
                        new_obj.dict() if hasattr(new_obj, "dict") else new_obj.__dict__
                    )

                return root_validator(pre=False)(wrapper_after)

        return decorator
