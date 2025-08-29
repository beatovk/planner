"""
Universal places fetcher.
"""

from typing import List, Dict, Any, Optional
from packages.wp_models.place import Place
from packages.wp_core.db import get_engine
from sqlalchemy import text
import json


class UniversalPlacesFetcher:
    """Universal fetcher for places from database."""

    def __init__(self):
        """Initialize the fetcher."""
        pass

    def get_supported_categories(self) -> List[str]:
        """Get list of supported place categories."""
        return [
            "markets",
            "food_dining", 
            "art_exhibits",
            "entertainment",
            "wellness",
            "shopping",
            "cafe",
            "restaurant",
            "bar",
            "spa",
            "museum",
            "gallery"
        ]

    def fetch(
        self, 
        city: str, 
        category: Optional[str] = None, 
        limit: Optional[int] = None
    ) -> List[Place]:
        """Fetch places from database."""
        try:
            engine = get_engine()
            
            # Базовый запрос - ищем по address, так как city пустое
            query = """
                SELECT 
                    id, name, description, city, address,
                    semantic_tags as tags, flags, rating, 
                    price_range, 
                    google_maps_url, geo_lat, geo_lng,
                    domain as source, semantic_core as category
                FROM places 
                WHERE address LIKE :city_pattern
            """
            params = {"city_pattern": f"%{city}%"}
            
            # Добавляем фильтр по категории если указана
            if category:
                query += " AND (flags LIKE :flags_pattern OR semantic_core LIKE :category_pattern)"
                params["flags_pattern"] = f"%{category}%"
                params["category_pattern"] = f"%{category}%"
            
            # Добавляем лимит
            if limit:
                query += f" LIMIT {limit}"
            else:
                query += " LIMIT 50"
            
            with engine.connect() as conn:
                result = conn.execute(text(query), params)
                rows = result.fetchall()
                
                places = []
                for row in rows:
                    try:
                        # Парсим JSON поля
                        tags = json.loads(row.tags) if row.tags else []
                        flags = json.loads(row.flags) if row.flags else []
                        
                        # Создаем Place объект
                        place = Place(
                            id=row.id,
                            name=row.name or "Unknown Place",
                            description=row.description or "",
                            city=row.city or city,
                            address=row.address or "",
                            lat=row.geo_lat or 13.7563,  # Bangkok default
                            lon=row.geo_lng or 100.5018,  # Bangkok default
                            tags=tags,
                            flags=flags,
                            rating=row.rating or 0.0,
                            price_range=row.price_range or "",
                            google_maps_url=row.google_maps_url or "",
                            source=row.source or "database",
                            category=row.category or category
                        )
                        places.append(place)
                        
                    except Exception as e:
                        print(f"Error creating Place from row {row.id}: {e}")
                        continue
                
                print(f"Fetched {len(places)} places from database for {city}:{category}")
                return places
                
        except Exception as e:
            print(f"Error fetching places from database: {e}")
            return []

    def fetch_places(
        self, city: str, category: str = None, limit: int = 50
    ) -> List[Place]:
        """Alias for fetch method."""
        return self.fetch(city, category, limit)
