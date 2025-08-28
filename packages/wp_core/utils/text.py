from __future__ import annotations

import html
import re


def html_unescape(value: str) -> str:
    return html.unescape(value)


def collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value)


def normalize_text(value: str) -> str:
    return collapse_spaces(html_unescape(value.strip()))


def safe_truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    truncated = value[:limit]
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return truncated.rstrip() + "…"


def norm_tag(value: str) -> str:
    return normalize_text(value).lower()
