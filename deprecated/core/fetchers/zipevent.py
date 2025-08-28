from __future__ import annotations

import re
import time
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from .interface import FetcherInterface
from .validator import ensure_events
from ..logging import logger
from ..events import Event


class ZipeventFetcher(FetcherInterface):
    """
    Zipevent event fetcher.
    Strategy:
      - Input URLs come from a seed list (env/config) or discovery pages.
      - For each event page: extract JSON-LD Event; fallback to CSS.
    """

    SOURCE = "zipevent"
    BASE = "https://www.zipeventapp.com"

    def __init__(self, *, seeds: Optional[List[str]] = None, session: Optional[requests.Session] = None, throttle: float = 0.5) -> None:
        self.seeds = seeds or []
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "WeekPlannerBot/1.0 (+https://example.com)"})
        self.throttle = throttle

    def fetch(self, category: Optional[str] = None, limit: Optional[int] = None) -> List[Event]:
        try:
            raw = self._raw_events(category=category, limit=limit)
        except Exception as exc:  # pragma: no cover
            logger.warning("%s fetch failed: %s", self.SOURCE, exc)
            return []
        return ensure_events(raw, source_name=self.SOURCE)

    # --- internals ---
    def _raw_events(self, category: Optional[str] = None, limit: Optional[int] = None) -> List[dict]:
        urls = list(self.seeds)
        # NOTE: при желании можно добавить лёгкое discovery с «похожих» страниц/хештегов.
        out: List[dict] = []
        for url in urls[: limit or len(urls)]:
            try:
                time.sleep(self.throttle)
                html = self.session.get(url, timeout=10).text
                out.append(self._parse_event_page(html, page_url=url))
            except Exception as exc:  # pragma: no cover
                logger.warning("zipevent: error on %s: %s", url, exc)
        return [e for e in out if e]

    def _parse_event_page(self, html: str, *, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "html.parser")

        # 1) JSON-LD
        data = self._jsonld_event(soup)
        title = (data.get("name") or "").strip() if data else ""
        start = (data.get("startDate") or "").strip() if data else None
        end = (data.get("endDate") or "").strip() if data else None
        image = data.get("image") if data else None
        venue = ""
        if data and isinstance(data.get("location"), dict):
            venue = (data["location"].get("name") or "").strip()

        # 2) Fallback CSS (дата/время, место)
        if not title:
            h = soup.find(["h1", "h2"])
            title = h.get_text(strip=True) if h else ""
        if not venue:
            venue_block = soup.find(string=re.compile(r"Location Details|LOCATION", re.I))
            if venue_block:
                v = venue_block.find_parent().find_next("h3")
                if v:
                    venue = v.get_text(strip=True)
        if not start:
            # Ищем паттерны дат на странице (например "7 Aug 2025" и т.п.)
            text = soup.get_text(" ", strip=True)
            m = re.search(r"(\d{1,2}\s+\w+\s+\d{4})", text, re.I)
            if m:
                start = m.group(1)

        if not title or not page_url:
            return None

        return {
            "id": page_url,  # уникален в рамках источника
            "title": title,
            "url": page_url,
            "source": self.SOURCE,
            "image": image,
            "start": start,
            "end": end,
            "venue": venue or None,
        }

    def _jsonld_event(self, soup: BeautifulSoup) -> Optional[dict]:
        import json
        for tag in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(tag.string or "{}")
            except Exception:
                continue
            # Может быть массивом/графом
            candidates = data if isinstance(data, list) else data.get("@graph") or [data]
            for item in candidates:
                t = (item.get("@type") or item.get("type") or "")
                if isinstance(t, list):
                    is_event = any("Event" in x for x in t)
                else:
                    is_event = "Event" in t
                if is_event:
                    return item
        return None
