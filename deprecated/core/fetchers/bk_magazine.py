from __future__ import annotations

from typing import List, Optional

from bs4 import BeautifulSoup
from typing import Dict, List
from ..extractors.jsonld import extract_events_from_jsonld
from ..normalize.datetime import normalize_start_end
from ..normalize.image import choose_image
from ..normalize.attrs import infer_attrs, enrich_tags

from .interface import FetcherInterface
from .validator import ensure_events
from ..events import Event
from ..logging import logger


class BKMagazineFetcher(FetcherInterface):
    """Fetcher for the BK Magazine website."""
    name = "bk_magazine"
    SELECTORS: Dict[str, str] = {
        "card": ".event",
        "title": ".title",
        "url": ".url",
        "img": "img",
    }

    def fetch(
        self, category: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Event]:
        try:
            raw = self._raw_events(category=category, limit=limit)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("%s fetch failed: %s", self.name, exc)
            return []
        return ensure_events(raw, source_name=self.name, limit=limit)

    def _raw_events(
        self, category: Optional[str] = None, limit: Optional[int] = None
    ) -> List[dict]:
        """Return raw event dictionaries before validation."""
        return []

    def _parse_page(self, html: str) -> List[dict]:
        """Parse a single HTML page into raw event dictionaries."""
        # 1) JSON-LD приоритет
        jl = extract_events_from_jsonld(html)
        if jl:
            for e in jl:
                e.setdefault("source", self.name)
                e["image"] = choose_image(html, e.get("image"))
                attrs = infer_attrs(e.get("title", ""), e.get("desc"))
                e["attrs"] = attrs
                e["tags"] = enrich_tags(e.get("tags") or [], e.get("editor_labels") or [])
            return jl
        # 2) CSS fallback
        soup = BeautifulSoup(html, "html.parser")
        events: List[dict] = []
        for card in soup.select(self.SELECTORS["card"]):
            img = card.select_one(self.SELECTORS["img"])
            raw_start = card.get("data-start")
            raw_end = card.get("data-end")
            time_str = (card.get("data-range") or card.get("data-time") or
                        (card.select_one(".time") and card.select_one(".time").get_text(strip=True)))
            start_dt, end_dt, time_str_out = normalize_start_end(raw_start, raw_end, time_str)
            title = (t := card.select_one(self.SELECTORS["title"])) and t.get_text(strip=True) or ""
            desc = None  # если в карточке есть описание — вытащи аналогично
            event = {
                "id": card.get("data-id", ""),
                "title": title,
                "url": (u := card.select_one(self.SELECTORS["url"])) and u.get("href") or None,
                "image": choose_image(html, img["src"] if img else None),
                "start": start_dt,
                "end": end_dt,
                "time_str": time_str_out,
                "venue": card.get("data-venue"),
                "source": self.name,
            }
            event["attrs"] = infer_attrs(title, desc)
            event["tags"] = enrich_tags([])
            events.append(event)
        return events


