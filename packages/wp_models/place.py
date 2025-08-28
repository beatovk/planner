from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from packages.wp_core.pydantic_compat import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    IS_PYDANTIC_V2,
    field_validator,
    model_validator,
)
from packages.wp_core.utils.text import norm_tag, normalize_text, safe_truncate


class Place(BaseModel):
    id: str
    source: str
    city: str
    name: str
    description: Optional[str] = None
    url: Optional[AnyUrl] = None
    image_url: Optional[AnyUrl] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    area: Optional[str] = None
    price_level: Optional[int] = None  # 0..4
    tags: List[str] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)  # наши 11 флагов
    popularity: Optional[float] = 0.0
    vec: Optional[List[float]] = None  # 384D, как у событий
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    if IS_PYDANTIC_V2:
        model_config = ConfigDict(extra="allow")
    else:
        class Config:
            extra = "allow"

    @field_validator(
        "id",
        "name",
        "description",
        "address",
        "area",
        "source",
        mode="before",
    )
    def _norm_strings(cls, v):
        if v is None:
            return v
        return normalize_text(str(v))

    @field_validator("url", "image_url", mode="before")
    def _norm_url(cls, v):
        if v is None:
            return v
        from urllib.parse import urlparse
        v = normalize_text(str(v))
        if not v:
            return v
        # протокол-relative //example.com => https://example.com
        if v.startswith("//"):
            return "https:" + v
        # уважать известные схемы и data/mailto/tel
        parsed = urlparse(v)
        if not parsed.scheme:
            return "https://" + v.lstrip("/")
        return v

    @field_validator("tags", "flags", mode="before")
    def _norm_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            v = [v]
        result: List[str] = []
        seen = set()
        for item in v:
            norm = norm_tag(str(item))
            if norm and norm not in seen:
                seen.add(norm)
                result.append(norm)
        return result

    @field_validator("price_level", mode="before")
    def _norm_price_level(cls, v):
        if v is None:
            return None
        try:
            level = int(v)
            return max(0, min(4, level))  # Ограничиваем 0-4
        except (ValueError, TypeError):
            return None

    @field_validator("lat", "lon", mode="before")
    def _norm_coordinates(cls, v):
        if v is None:
            return v
        try:
            coord = float(v)
            # Проверяем разумные границы координат
            if -90 <= coord <= 90:
                return round(coord, 6)
            return None
        except (ValueError, TypeError):
            return None

    def identity_key(self) -> str:
        """Генерирует уникальный ключ для дедупликации мест."""
        base = re.sub(r"[^a-z0-9]+", "-", f"{self.name}-{self.city}".lower()).strip("-")
        domain = ""
        if self.url:
            m = re.search(r"https?://([^/]+)/?", str(self.url))
            domain = m.group(1) if m else ""
        geo = f"{round(self.lat,3)}_{round(self.lon,3)}" if self.lat and self.lon else ""
        return f"{base}::{domain}::{geo}"

    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует Place в словарь для БД."""
        return {
            "id": self.id,
            "source": self.source,
            "city": self.city,
            "name": self.name,
            "description": self.description,
            "url": str(self.url) if self.url else None,
            "image_url": str(self.image_url) if self.image_url else None,
            "address": self.address,
            "lat": self.lat,
            "lon": self.lon,
            "area": self.area,
            "price_level": self.price_level,
            "tags": self.tags,
            "flags": self.flags,
            "popularity": self.popularity,
            "vec": self.vec,
            "identity_key": self.identity_key(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Place":
        """Создает Place из словаря БД."""
        # Обработка JSON полей
        if isinstance(data.get("tags"), str):
            import json
            try:
                data["tags"] = json.loads(data["tags"])
            except (json.JSONDecodeError, TypeError):
                data["tags"] = []
        
        if isinstance(data.get("flags"), str):
            import json
            try:
                data["flags"] = json.loads(data["flags"])
            except (json.JSONDecodeError, TypeError):
                data["flags"] = []
        
        if isinstance(data.get("vec"), str):
            import json
            try:
                data["vec"] = json.loads(data["vec"])
            except (json.JSONDecodeError, TypeError):
                data["vec"] = None
        
        # Обработка дат
        if isinstance(data.get("created_at"), str):
            try:
                data["created_at"] = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                data["created_at"] = datetime.now(timezone.utc)
        
        if isinstance(data.get("updated_at"), str):
            try:
                data["updated_at"] = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                data["updated_at"] = datetime.now(timezone.utc)
        
        return cls(**data)
