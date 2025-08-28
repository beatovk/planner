from __future__ import annotations
from typing import List, Optional, Dict, Any, Iterable, Tuple
import asyncio
import os
import re
import hashlib
import httpx
from bs4 import BeautifulSoup

from .place_interface import FetcherPlaceInterface
from ..models_places.place import Place
from ..logging import logger
from ..query.place_facets import map_place_to_flags


class TimeOutBKKPlacesFetcher(FetcherPlaceInterface):
    """Time Out Bangkok: places discovery → detail parsing → normalized Place."""
    name = "timeout_bkk_places"
    SOURCE = "timeout_bkk"
    CITY = "bangkok"
    
    # URL для мест (не событий)
    _LISTING_URLS = [
        "https://www.timeout.com/bangkok/restaurants",
        "https://www.timeout.com/bangkok/bars",
        "https://www.timeout.com/bangkok/attractions",
        "https://www.timeout.com/bangkok/shopping",
        "https://www.timeout.com/bangkok/arts-culture",
        "https://www.timeout.com/bangkok/wellness",
    ]
    
    _CONCURRENCY = int(os.environ.get("TO_CONCURRENCY", "6"))
    _TIMEOUT = float(os.environ.get("TO_TIMEOUT_S", "8"))
    _UA = os.environ.get("TO_UA", "Mozilla/5.0 (WeekPlanner/TimeoutPlacesFetcher)")

    # Селекторы для мест
    SELECTORS: Dict[str, str] = {
        "card": "article.tile, .card, .listing-item",
        "title": "h3, h2, h1, .title, .name",
        "url": "a[href*='/bangkok/']",
        "img": "img",
        "summary": "p, .description, .summary",
        "tags": "ul li, .tag, .category, .cuisine",
        "address": ".address, .location, .area",
        "price": ".price, .cost, .budget",
    }

    def fetch(self, city: str, category: Optional[str] = None, limit: Optional[int] = None) -> List[Place]:
        if city.lower() != "bangkok":
            return []
            
        try:
            raw = asyncio.run(self._gather(category=category, limit=limit))
        except Exception as exc:
            logger.warning("timeout_bkk_places fetch failed: %s", exc)
            return []
        return raw

    async def _gather(self, category: Optional[str], limit: Optional[int]) -> List[Place]:
        # 1) собрать урлы карточек мест
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
        
        # 2) параллельно тянуть детали мест
        sem = asyncio.Semaphore(self._CONCURRENCY)
        async with httpx.AsyncClient(timeout=self._TIMEOUT, headers={"User-Agent": self._UA}) as client:
            places = []
            for url in card_urls:
                try:
                    result = await self._fetch_detail(client, sem, url)
                    if result:
                        places.append(result)
                except Exception as e:
                    logger.warning(f"Error processing place {url}: {e}")
        
        return places

    def _listing_urls_for(self, category: Optional[str]) -> List[str]:
        if category:
            # Фильтруем URL по категории
            category_urls = {
                "food_dining": [
                    "https://www.timeout.com/bangkok/restaurants",
                    "https://www.timeout.com/bangkok/bars",
                ],
                "art_exhibits": [
                    "https://www.timeout.com/bangkok/arts-culture",
                ],
                "markets": [
                    "https://www.timeout.com/bangkok/shopping",
                ],
                "yoga_wellness": [
                    "https://www.timeout.com/bangkok/wellness",
                ],
                "parks": [
                    "https://www.timeout.com/bangkok/attractions",
                ],
            }
            return category_urls.get(category, self._LISTING_URLS)
        return list(self._LISTING_URLS)

    def _extract_listing_links(self, html: str) -> List[str]:
        soup = BeautifulSoup(html or "", "html.parser")
        links: List[str] = []
        
        # Ищем ссылки на места в Timeout Bangkok
        selectors = [
            "a[href*='/bangkok/']",
            "article a[href]",
            ".card a[href]",
            ".tile a[href]",
        ]
        
        for selector in selectors:
            for a in soup.select(selector):
                href = a.get("href", "").strip()
                if href and href.startswith("/"):
                    href = f"https://www.timeout.com{href}"
                if href and "/bangkok/" in href and href not in links:
                    links.append(href)
        
        return links

    async def _get(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        """Получить HTML страницы."""
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    async def _fetch_detail(self, client: httpx.AsyncClient, sem: asyncio.Semaphore, url: str) -> Optional[Place]:
        """Получить детали места."""
        async with sem:
            try:
                html = await self._get(client, url)
                if not html:
                    return None
                
                return self._parse_place_detail(html, url)
            except Exception as e:
                logger.warning(f"Error parsing place {url}: {e}")
                return None

    def _parse_place_detail(self, html: str, url: str) -> Optional[Place]:
        """Парсинг деталей места."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Извлекаем основную информацию
        title = self._extract_text(soup, self.SELECTORS["title"])
        if not title:
            return None
        
        description = self._extract_text(soup, self.SELECTORS["summary"])
        image_url = self._extract_image(soup)
        address = self._extract_text(soup, self.SELECTORS["address"])
        price_level = self._extract_price_level(soup)
        tags = self._extract_tags(soup)
        
        # Генерируем ID
        place_id = self._generate_id(title, url)
        
        # Создаем базовый объект места
        place_data = {
            "id": place_id,
            "source": self.SOURCE,
            "city": self.CITY,
            "name": title,
            "description": description,
            "url": url,
            "image_url": image_url,
            "address": address,
            "price_level": price_level,
            "tags": tags,
            "popularity": 0.0,  # Будет рассчитано позже
        }
        
        # Определяем флаги на основе контента
        flags = map_place_to_flags(place_data)
        place_data["flags"] = flags
        
        # Попытка извлечь координаты (если есть в JSON-LD или мета-тегах)
        lat, lon = self._extract_coordinates(soup)
        if lat and lon:
            place_data["lat"] = lat
            place_data["lon"] = lon
        
        # Попытка извлечь район
        area = self._extract_area(soup, address)
        if area:
            place_data["area"] = area
        
        try:
            return Place(**place_data)
        except Exception as e:
            logger.warning(f"Failed to create Place object: {e}")
            return None

    def _extract_text(self, soup: BeautifulSoup, selector: str) -> Optional[str]:
        """Извлечь текст по селектору."""
        elements = soup.select(selector)
        if elements:
            return elements[0].get_text(strip=True)
        return None

    def _extract_image(self, soup: BeautifulSoup) -> Optional[str]:
        """Извлечь URL изображения."""
        img = soup.select_one(self.SELECTORS["img"])
        if img and img.get("src"):
            src = img["src"]
            if src.startswith("//"):
                return f"https:{src}"
            elif src.startswith("/"):
                return f"https://www.timeout.com{src}"
            elif src.startswith("http"):
                return src
        return None

    def _extract_price_level(self, soup: BeautifulSoup) -> Optional[int]:
        """Извлечь уровень цен."""
        price_text = self._extract_text(soup, self.SELECTORS["price"])
        if not price_text:
            return None
        
        # Простая эвристика для определения уровня цен
        price_lower = price_text.lower()
        if any(word in price_lower for word in ["cheap", "budget", "affordable"]):
            return 1
        elif any(word in price_lower for word in ["moderate", "mid-range"]):
            return 2
        elif any(word in price_lower for word in ["expensive", "luxury", "high-end"]):
            return 4
        else:
            return 2  # По умолчанию

    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Извлечь теги."""
        tags = []
        tag_elements = soup.select(self.SELECTORS["tags"])
        for element in tag_elements:
            tag_text = element.get_text(strip=True)
            if tag_text and len(tag_text) < 50:  # Фильтруем слишком длинные теги
                tags.append(tag_text)
        return tags[:10]  # Ограничиваем количество тегов

    def _extract_coordinates(self, soup: BeautifulSoup) -> Tuple[Optional[float], Optional[float]]:
        """Извлечь координаты из JSON-LD или мета-тегов."""
        # Ищем JSON-LD с координатами
        jsonld_scripts = soup.find_all("script", type="application/ld+json")
        for script in jsonld_scripts:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    lat = data.get("latitude") or data.get("lat")
                    lon = data.get("longitude") or data.get("lng") or data.get("lon")
                    if lat and lon:
                        return float(lat), float(lon)
            except (json.JSONDecodeError, (ValueError, TypeError)):
                continue
        
        # Ищем в мета-тегах
        lat_meta = soup.find("meta", {"name": "geo.position"})
        if lat_meta and lat_meta.get("content"):
            try:
                coords = lat_meta["content"].split(";")
                if len(coords) == 2:
                    return float(coords[0]), float(coords[1])
            except (ValueError, TypeError):
                pass
        
        return None, None

    def _extract_area(self, soup: BeautifulSoup, address: Optional[str]) -> Optional[str]:
        """Извлечь район из адреса или контента."""
        if address:
            # Простые эвристики для определения района
            area_keywords = [
                "sukhumvit", "silom", "siam", "ratchada", "thonglor", "ari", "asoke",
                "chidlom", "ploenchit", "ratchaprasong", "pratunam", "yaowarat",
                "chinatown", "khaosan", "banglamphu", "dusit", "chatuchak"
            ]
            
            address_lower = address.lower()
            for area in area_keywords:
                if area in address_lower:
                    return area.title()
        
        return None

    def _generate_id(self, title: str, url: str) -> str:
        """Генерирует уникальный ID для места."""
        # Используем хеш от названия и URL
        content = f"{title}:{url}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def get_supported_cities(self) -> List[str]:
        return ["bangkok"]

    def get_supported_categories(self) -> List[str]:
        return [
            "food_dining", "art_exhibits", "markets", "yoga_wellness", "parks",
            "electronic_music", "live_music", "jazz_blues", "rooftop", "workshops", "cinema"
        ]


def _dedup_stable(items: List[str]) -> List[str]:
    """Убирает дубликаты, сохраняя порядок."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
