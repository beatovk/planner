from __future__ import annotations

import hashlib
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


class Event(BaseModel):
    id: str
    title: str
    desc: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    time_str: Optional[str] = None
    venue: Optional[str] = None
    area: Optional[str] = None
    address: Optional[str] = None
    image: Optional[AnyUrl] = None
    url: AnyUrl
    price_min: Optional[float] = None
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    source: str
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attrs: Dict[str, Any] = Field(default_factory=dict)
    raw_html_ref: Optional[str] = None

    if IS_PYDANTIC_V2:
        model_config = ConfigDict(extra="allow")
    else:
        class Config:
            extra = "allow"

    @field_validator(
        "id",
        "title",
        "desc",
        "time_str",
        "venue",
        "area",
        "address",
        "source",
        "raw_html_ref",
        mode="before",
    )
    def _norm_strings(cls, v):
        if v is None:
            return v
        return normalize_text(str(v))

    @field_validator("url", "image", mode="before")
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

    @field_validator("categories", "tags", mode="before")
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

    @model_validator(mode="after")
    def _post(cls, obj: "Event"):
        if obj.attrs:
            def to_bool(x):
                if isinstance(x, bool):
                    return x
                if isinstance(x, (int, float)):
                    return x != 0
                s = str(x).strip().lower()
                if s in {"false", "0", "no", "off", "none", ""}:
                    return False
                if s in {"true", "1", "yes", "on"}:
                    return True
                return bool(x)
            obj.attrs = {k: to_bool(v) for k, v in obj.attrs.items()}
        if obj.desc:
            truncated = safe_truncate(obj.desc, 4000)
            if truncated != obj.desc:
                obj.attrs.setdefault("desc_full", obj.desc)
                obj.desc = truncated
        # мягкая попытка привести price_min к float
        if obj.price_min is not None and not isinstance(obj.price_min, (int, float)):
            try:
                obj.price_min = float(str(obj.price_min).replace(",", "."))
            except Exception:
                obj.price_min = None
        return obj

    def identity_key(self) -> str:
        title = normalize_text(self.title).lower()
        venue = normalize_text(self.venue) if self.venue else ""
        date = self.start.date().isoformat() if self.start else ""
        raw = "|".join([title, date, venue])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
