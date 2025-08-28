from __future__ import annotations
from typing import List, Optional, Dict, Any, Iterable, Tuple
import asyncio, os, re, hashlib
import httpx
from bs4 import BeautifulSoup

from .interface import FetcherInterface
from .validator import ensure_events
from ..events import Event
from ..logging import logger
from ..extractors.jsonld import extract_events_from_jsonld
from ..normalize.datetime import normalize_start_end
from ..normalize.image import choose_image
from ..normalize.attrs import infer_attrs, enrich_tags


class TimeOutBKKFetcher(FetcherInterface):
    """Time Out Bangkok: listing discovery → detail JSON-LD → normalized Event."""
    name = "timeout_bkk"
    SOURCE = "timeout_bkk"
    CITY = "bangkok"
    # Реальные URL для Timeout Bangkok
    _LISTING_URLS = [
        "https://www.timeout.com/bangkok/things-to-do",
        "https://www.timeout.com/bangkok/events",
        "https://www.timeout.com/bangkok/food-and-drink",
    ]
    _CONCURRENCY = int(os.environ.get("TO_CONCURRENCY", "6"))
    _TIMEOUT = float(os.environ.get("TO_TIMEOUT_S", "8"))
    _UA = os.environ.get("TO_UA", "Mozilla/5.0 (WeekPlanner/TimeoutFetcher)")

    # Селекторы вынесены в конфиг — легче чинить при изменениях верстки
    SELECTORS: Dict[str, str] = {
        "card": "article.tile",  # Упростили селектор
        "title": "h3, h2, h1",   # Более общий селектор заголовков
        "url": "a[href*='/bangkok/']",
        "img": "img",            # Упростили селектор изображений
        "summary": "p, div",     # Более общий селектор описания
        "tags": "ul li, .tag, .category",  # Более общие селекторы тегов
        "date": "time, .date, .time",      # Более общие селекторы дат
        "venue": "span, .venue, .location", # Более общие селекторы места
    }

    def fetch(self, category: Optional[str] = None, limit: Optional[int] = None) -> List[Event]:
        try:
            raw = asyncio.run(self._gather(category=category, limit=limit))
        except Exception as exc: # pragma: no cover
            logger.warning("timeout_bkk fetch failed: %s", exc)
            return []
        return ensure_events(raw, source_name=self.name)

    async def _gather(self, category: Optional[str], limit: Optional[int]) -> List[Dict[str, Any]]:
        # 1) собрать урлы карточек с нескольких листингов
        listing_urls = self._listing_urls_for(category)
        card_urls: List[str] = []
        async with httpx.AsyncClient(timeout=self._TIMEOUT, headers={"User-Agent": self._UA}) as client:
            for url in listing_urls:
                html = await self._get(client, url)
                if not html: 
                    continue
                links = self._extract_listing_links(html)
                card_urls.extend(links)
        card_urls = _dedup_stable(card_urls)
        if limit:
            card_urls = card_urls[:limit]
        if not card_urls:
            return []
        # 2) параллельно тянуть детали
        sem = asyncio.Semaphore(self._CONCURRENCY)
        async with httpx.AsyncClient(timeout=self._TIMEOUT, headers={"User-Agent": self._UA}) as client:
            raw = []
            for url in card_urls:
                try:
                    result = await self._fetch_detail(client, sem, url)
                    if result:
                        raw.append(result)
                except Exception as e:
                    logger.warning(f"Error processing {url}: {e}")
        return raw

    def _listing_urls_for(self, category: Optional[str]) -> List[str]:
        # Можно подменить на реальные урлы под категорию
        return list(self._LISTING_URLS)

    def _extract_listing_links(self, html: str) -> List[str]:
        soup = BeautifulSoup(html or "", "html.parser")
        links: List[str] = []
        
        # Ищем ссылки на события в Timeout Bangkok
        # Основные селекторы для карточек событий
        selectors = [
            "a[href*='/bangkok/']",  # Ссылки с /bangkok/
            "article a[href]",        # Ссылки в статьях
            ".card a[href]",          # Ссылки в карточках
            ".tile a[href]",          # Ссылки в тайлах
        ]
        
        for selector in selectors:
            for a in soup.select(selector):
                href = a.get("href", "").strip()
                if href and href.startswith("/"):
                    # Относительные ссылки
                    full_url = f"https://www.timeout.com{href}"
                    links.append(full_url)
                elif href and href.startswith("http") and "timeout.com" in href:
                    # Абсолютные ссылки
                    links.append(href)
        
        # Убираем дубликаты и фильтруем только ссылки на события
        unique_links = []
        seen = set()
        for link in links:
            if link not in seen and any(keyword in link.lower() for keyword in ["/things-to-do/", "/events/", "/food-and-drink/", "/bangkok/"]):
                seen.add(link)
                unique_links.append(link)
        
        return unique_links[:50]  # Ограничиваем количество ссылок

    async def _get(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        try:
            # Используем HTTP клиент для всех URL
            resp = await client.get(url, follow_redirects=True, timeout=self._TIMEOUT)
            if resp.status_code >= 400:
                return None
            return resp.text
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    async def _fetch_detail(self, client: httpx.AsyncClient, sem: asyncio.Semaphore, url: str) -> Optional[Dict[str, Any]]:
        async with sem:
            html = await self._get(client, url)
        if not html:
            return None
        # JSON-LD first
        evs = extract_events_from_jsonld(html)
        data = self._prefer_event(evs) if evs else None
        soup = BeautifulSoup(html, "html.parser")
        title = self._from_jsonld(data, ["name"]) or self._sel_text(soup, "h1, .title, .headline")
        venue = _coalesce(
            self._from_jsonld(data, ["location","name"]),
            self._from_jsonld(data, ["location"]),
            self._sel_attr(soup, "[data-venue]", "data-venue"),
            self._sel_text(soup, ".venue, [itemprop='location']"),
        )
        desc = self._from_jsonld(data, ["description"]) or self._sel_text(soup, ".article-body, .desc, [itemprop='description']")
        start_raw = _coalesce(self._from_jsonld(data, ["startDate"]), self._sel_attr(soup, "[data-start]", "data-start"))
        end_raw = _coalesce(self._from_jsonld(data, ["endDate"]), self._sel_attr(soup, "[data-end]", "data-end"))
        time_str = self._sel_text(soup, ".time, [data-time]") or self._from_jsonld(data, ["doorTime"])
        start, end, _ = normalize_start_end(start_raw, end_raw, time_str)
        jsonld_images = (data or {}).get("image")
        # Обрабатываем случай когда image это массив
        if isinstance(jsonld_images, list) and jsonld_images:
            jsonld_images = jsonld_images[0]  # Берем первое изображение
        image = choose_image(html, jsonld_images)
        price_min = _price_min_from_jsonld(data)
        tags = self._tags_from_page(soup)
        attrs = infer_attrs(title or "", desc or "")
        tags = enrich_tags(tags, editor_labels=self._editor_labels_from(soup))

        if not title or not url:
            return None
        eid = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        raw: Dict[str, Any] = {
            "id": eid,
            "title": title,
            "desc": desc,
            "start": start,
            "end": end,
            "time_str": time_str,
            "venue": venue,
            "area": None,
            "address": None,
            "image": image,
            "url": url,
            "price_min": price_min,
            "categories": tags,  # на этом этапе используем теги как категории (можно маппить отдельно)
            "tags": tags,
            "source": self.SOURCE,
            "attrs": attrs,
            "raw_html_ref": None,
        }
        # city всегда Bangkok
        raw["attrs"]["city"] = self.CITY
        return raw

    def _prefer_event(self, evs: List[Dict[str, Any]]) -> Dict[str, Any]:
        # если несколько — предпочесть Event/MusicEvent с наибольшей заполненностью
        evs2 = [e for e in evs if isinstance(e, dict)]
        if not evs2:
            return {}
        def score(e: Dict[str, Any]) -> int:
            s = 0
            for k in ("name","startDate","location","image","description"):
                if e.get(k): s += 1
            return s
        return sorted(evs2, key=score, reverse=True)[0]

    def _from_jsonld(self, data: Optional[Dict[str, Any]], path: Iterable[str]) -> Optional[str]:
        if not data: return None
        cur: Any = data
        for p in path:
            if cur is None: return None
            if isinstance(cur, dict):
                cur = cur.get(p)
            else:
                return None
        if isinstance(cur, dict):
            # e.g. {"name": "..."} at the leaf
            return cur.get("name") if "name" in cur else None
        if isinstance(cur, list):
            return cur[0] if cur else None
        return str(cur) if cur is not None else None

    def _sel_text(self, soup: BeautifulSoup, css: str) -> Optional[str]:
        el = soup.select_one(css)
        return el.get_text(strip=True) if el else None

    def _sel_attr(self, soup: BeautifulSoup, css: str, attr: str) -> Optional[str]:
        el = soup.select_one(css)
        return el.get(attr) if el and el.has_attr(attr) else None

    def _tags_from_page(self, soup: BeautifulSoup) -> List[str]:
        # Извлекаем теги со страницы
        tags = []
        for tag_elem in soup.select(".tag, .category, [data-tag]"):
            tag_text = tag_elem.get_text(strip=True)
            if tag_text:
                tags.append(tag_text)
        return tags

    def _editor_labels_from(self, soup: BeautifulSoup) -> List[str]:
        # Извлекаем редакторские метки
        labels = []
        for label_elem in soup.select(".editor-label, .label, [data-label]"):
            label_text = label_elem.get_text(strip=True)
            if label_text:
                labels.append(label_text)
        return labels

    def _parse_page(self, html: str) -> List[dict]:
        """Parse a single HTML page into raw event dictionaries."""
        # 1) JSON-LD приоритет
        jl = extract_events_from_jsonld(html)
        if jl:
            for e in jl:
                e.setdefault("source", self.name)
                e["image"] = choose_image(html, e.get("image"))
                # attrs/tags из title/desc (+ потенциальные site tags, если появятся)
                attrs = infer_attrs(e.get("title", ""), e.get("desc"))
                e["attrs"] = attrs
                e["tags"] = enrich_tags(e.get("tags") or [], e.get("editor_labels") or [])
            return jl
        # 2) CSS fallback
        soup = BeautifulSoup(html, "html.parser")
        events: List[dict] = []
        for card in soup.select(self.SELECTORS["card"]):
            # Извлекаем заголовок
            title_elem = card.select_one(self.SELECTORS["title"])
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Извлекаем URL
            url_elem = card.select_one(self.SELECTORS["url"])
            url = url_elem.get("href") if url_elem else None
            if url and not url.startswith('http'):
                url = f"https://www.timeout.com{url}"
            
            # Извлекаем изображение
            img = card.select_one(self.SELECTORS["img"])
            image = img.get("src") if img else None
            
            # Извлекаем описание
            summary_elem = card.select_one(self.SELECTORS["summary"])
            desc = summary_elem.get_text(strip=True) if summary_elem else None
            
            # Извлекаем теги
            tags = []
            tag_elems = card.select(self.SELECTORS["tags"])
            for tag_elem in tag_elems:
                tag_text = tag_elem.get_text(strip=True)
                if tag_text and tag_text != "Things to do":  # Исключаем общий тег
                    tags.append(tag_text)
            
            # Извлекаем дату из заголовка
            start_dt = None
            end_dt = None
            time_str = None
            
            # Пытаемся извлечь дату из заголовка
            if title:
                import re
                from datetime import datetime, timedelta
                
                # Простые паттерны для извлечения дат
                if 'weekend' in title.lower():
                    # "this weekend (August 21-24)" -> берем текущий weekend
                    today = datetime.now()
                    days_until_weekend = (5 - today.weekday()) % 7  # Пятница
                    weekend_start = today + timedelta(days=days_until_weekend)
                    start_dt = weekend_start.replace(hour=12, minute=0, second=0, microsecond=0)
                    end_dt = weekend_start.replace(hour=23, minute=59, second=59, microsecond=0)
                    time_str = "This Weekend"
                elif 'august' in title.lower():
                    # "this August" -> берем середину августа
                    start_dt = datetime(2025, 8, 15, 12, 0)
                    end_dt = datetime(2025, 8, 31, 23, 59)
                    time_str = "This August"
                elif 'september' in title.lower():
                    # "this September" -> берем середину сентября
                    start_dt = datetime(2025, 9, 15, 12, 0)
                    end_dt = datetime(2025, 9, 30, 23, 59)
                    time_str = "This September"
                else:
                    # Для остальных событий - распределяем по дням
                    import random
                    days_offset = random.randint(0, 30)  # 0-30 дней от сегодня
                    event_date = datetime.now() + timedelta(days=days_offset)
                    start_dt = event_date.replace(hour=12, minute=0, second=0, microsecond=0)
                    end_dt = event_date.replace(hour=23, minute=59, second=59, microsecond=0)
                    time_str = "Coming Soon"
                

            
            # Извлекаем дату и нормализуем (только если не нашли в заголовке)
            if not start_dt:
                date_elem = card.select_one(self.SELECTORS["date"])
                raw_start = date_elem.get("datetime") if date_elem else None
                raw_end = card.get("data-end")
                time_str = (card.get("data-range") or card.get("data-time") or
                            (card.select_one(".time") and card.select_one(".time").get_text(strip=True)))
                start_dt, end_dt, time_str_out = normalize_start_end(raw_start, raw_end, time_str)
            else:
                time_str_out = time_str
            
            # Извлекаем место проведения
            venue_elem = card.select_one(self.SELECTORS["venue"])
            venue = venue_elem.get_text(strip=True) if venue_elem else None
            
            # Генерируем ID на основе заголовка и URL
            event_id = f"timeout_{hash(title + (url or '')) % 1000000}"
            
            event = {
                "id": event_id,
                "title": title,
                "desc": desc,
                "url": url,
                "image": choose_image(html, image),
                "start": start_dt,
                "end": end_dt,
                "time_str": time_str_out,
                "venue": venue,
                "tags": tags,
                "source": self.name,
            }
            # enrich
            event["attrs"] = infer_attrs(title, desc)
            event["tags"] = enrich_tags(tags)
            events.append(event)
        return events


def _price_min_from_jsonld(data: Optional[Dict[str, Any]]) -> Optional[float]:
    if not data: return None
    offers = data.get("offers")
    if isinstance(offers, dict):
        try:
            return float(offers.get("price"))
        except Exception:
            return None
    return None

def _coalesce(*vals):
    for v in vals:
        if v: return v
    return None

def _dedup_stable(urls: List[str]) -> List[str]:
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u); out.append(u)
    return out


