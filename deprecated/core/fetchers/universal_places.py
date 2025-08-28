from __future__ import annotations
from typing import List, Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .place_interface import FetcherPlaceInterface
from .timeout_bkk_places import TimeOutBKKPlacesFetcher
from .bk_magazine_places import BKMagazinePlacesFetcher
from ..models_places.place import Place
from ..logging import logger


class UniversalPlacesFetcher(FetcherPlaceInterface):
    """Universal places fetcher that combines multiple sources."""
    name = "universal_places"
    
    def __init__(self):
        self.fetchers = [
            TimeOutBKKPlacesFetcher(),
            BKMagazinePlacesFetcher(),
        ]
    
    def fetch(self, city: str, category: Optional[str] = None, limit: Optional[int] = None) -> List[Place]:
        """Fetch places from all available sources."""
        all_places = []
        
        # Запускаем все fetcher'ы параллельно
        with ThreadPoolExecutor(max_workers=len(self.fetchers)) as executor:
            futures = []
            for fetcher in self.fetchers:
                if city.lower() in [c.lower() for c in fetcher.get_supported_cities()]:
                    future = executor.submit(fetcher.fetch, city, category, limit)
                    futures.append((fetcher.name, future))
            
            # Собираем результаты
            for fetcher_name, future in futures:
                try:
                    places = future.result()
                    if places:
                        logger.info(f"Fetched {len(places)} places from {fetcher_name}")
                        all_places.extend(places)
                except Exception as e:
                    logger.warning(f"Fetcher {fetcher_name} failed: {e}")
        
        # Дедупликация по identity_key
        unique_places = self._deduplicate_places(all_places)
        
        # Применяем лимит
        if limit:
            unique_places = unique_places[:limit]
        
        logger.info(f"Total unique places fetched: {len(unique_places)}")
        return unique_places
    
    def _deduplicate_places(self, places: List[Place]) -> List[Place]:
        """Remove duplicate places based on identity_key."""
        seen_keys = set()
        unique_places = []
        
        for place in places:
            identity_key = place.identity_key()
            if identity_key not in seen_keys:
                seen_keys.add(identity_key)
                unique_places.append(place)
        
        return unique_places
    
    def get_supported_cities(self) -> List[str]:
        """Get all supported cities from all fetchers."""
        cities = set()
        for fetcher in self.fetchers:
            cities.update(fetcher.get_supported_cities())
        return list(cities)
    
    def get_supported_categories(self) -> List[str]:
        """Get all supported categories from all fetchers."""
        categories = set()
        for fetcher in self.fetchers:
            categories.update(fetcher.get_supported_categories())
        return list(categories)
    
    def get_fetcher_stats(self) -> Dict[str, Any]:
        """Get statistics about available fetchers."""
        stats = {
            "total_fetchers": len(self.fetchers),
            "fetchers": []
        }
        
        for fetcher in self.fetchers:
            fetcher_stats = {
                "name": fetcher.name,
                "source": getattr(fetcher, 'SOURCE', 'unknown'),
                "cities": fetcher.get_supported_cities(),
                "categories": fetcher.get_supported_categories(),
            }
            stats["fetchers"].append(fetcher_stats)
        
        return stats
