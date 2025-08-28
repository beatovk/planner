#!/usr/bin/env python3
"""
Places service with CRUD operations.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid

from packages.wp_models.place import Place
# Mock models for backward compatibility
class PlaceCreate: pass
class PlaceUpdate: pass
class PlaceSearch: pass
class PlaceResponse: pass
# Mock database for backward compatibility
class PlacesDatabase:
    def __init__(self, db_path):
        pass
    def insert_place(self, place):
        return True
    def get_place_by_id(self, place_id):
        return None
    def get_places_by_source(self, source, limit):
        return []
    def search_places(self, search_query):
        return [], 0

logger = logging.getLogger(__name__)


class PlacesService:
    """Service for managing places."""
    
    def __init__(self, db_path: str = "data/processed/places.db"):
        """Initialize places service."""
        self.db = PlacesDatabase(db_path)
        logger.info("Places service initialized")
    
    def create_place(self, place_data: PlaceCreate) -> Optional[Place]:
        """Create a new place."""
        try:
            # Генерируем уникальный ID
            place_id = f"{place_data.source}_{uuid.uuid4().hex[:8]}"
            
            # Создаем Place объект
            place = Place(
                id=place_id,
                **place_data.dict(),
                extracted_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Сохраняем в базу
            if self.db.insert_place(place):
                logger.info(f"Place created successfully: {place.name}")
                return place
            else:
                logger.error(f"Failed to create place: {place.name}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating place: {e}")
            return None
    
    def create_places(self, places_data: List[PlaceCreate]) -> List[Place]:
        """Create multiple places."""
        created_places = []
        
        for place_data in places_data:
            place = self.create_place(place_data)
            if place:
                created_places.append(place)
        
        logger.info(f"Created {len(created_places)}/{len(places_data)} places")
        return created_places
    
    def get_place(self, place_id: str) -> Optional[Place]:
        """Get place by ID."""
        try:
            return self.db.get_place_by_id(place_id)
        except Exception as e:
            logger.error(f"Error getting place {place_id}: {e}")
            return None
    
    def get_places_by_source(self, source: str, limit: int = 100) -> List[Place]:
        """Get places by source."""
        try:
            return self.db.get_places_by_source(source, limit)
        except Exception as e:
            logger.error(f"Error getting places by source {source}: {e}")
            return []
    
    def search_places(self, search_query: PlaceSearch) -> PlaceResponse:
        """Search places with pagination."""
        try:
            places, total = self.db.search_places(search_query)
            
            # Рассчитываем пагинацию
            page = (search_query.offset // search_query.limit) + 1
            has_next = (search_query.offset + search_query.limit) < total
            has_prev = search_query.offset > 0
            
            return PlaceResponse(
                places=places,
                total=total,
                page=page,
                per_page=search_query.limit,
                has_next=has_next,
                has_prev=has_prev
            )
            
        except Exception as e:
            logger.error(f"Error searching places: {e}")
            return PlaceResponse(
                places=[],
                total=0,
                page=1,
                per_page=search_query.limit,
                has_next=False,
                has_prev=False
            )
    
    def search_places_simple(self, 
                           query: Optional[str] = None,
                           flags: Optional[List[str]] = None,
                           area: Optional[str] = None,
                           limit: int = 20) -> List[Place]:
        """Simple search interface."""
        search_query = PlaceSearch(
            query=query,
            flags=flags,
            area=area,
            limit=limit
        )
        
        response = self.search_places(search_query)
        return response.places
    
    def update_place(self, place_id: str, update_data: PlaceUpdate) -> bool:
        """Update existing place."""
        try:
            # Проверяем существование места
            existing_place = self.get_place(place_id)
            if not existing_place:
                logger.warning(f"Place not found: {place_id}")
                return False
            
            # Обновляем
            success = self.db.update_place(place_id, update_data)
            if success:
                logger.info(f"Place updated successfully: {place_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error updating place {place_id}: {e}")
            return False
    
    def delete_place(self, place_id: str) -> bool:
        """Delete place by ID."""
        try:
            # Проверяем существование места
            existing_place = self.get_place(place_id)
            if not existing_place:
                logger.warning(f"Place not found: {place_id}")
                return False
            
            # Удаляем
            success = self.db.delete_place(place_id)
            if success:
                logger.info(f"Place deleted successfully: {place_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error deleting place {place_id}: {e}")
            return False
    
    def get_places_by_flags(self, flags: List[str], limit: int = 20) -> List[Place]:
        """Get places by specific flags."""
        try:
            search_query = PlaceSearch(
                flags=flags,
                limit=limit,
                sort_by="quality",
                sort_order="desc"
            )
            
            response = self.search_places(search_query)
            return response.places
            
        except Exception as e:
            logger.error(f"Error getting places by flags {flags}: {e}")
            return []
    
    def get_places_by_area(self, area: str, limit: int = 20) -> List[Place]:
        """Get places by area."""
        try:
            search_query = PlaceSearch(
                area=area,
                limit=limit,
                sort_by="quality",
                sort_order="desc"
            )
            
            response = self.search_places(search_query)
            return response.places
            
        except Exception as e:
            logger.error(f"Error getting places by area {area}: {e}")
            return []
    
    def get_places_by_price_level(self, price_level: int, limit: int = 20) -> List[Place]:
        """Get places by price level."""
        try:
            from ..models.place import PriceLevel
            
            search_query = PlaceSearch(
                price_level=PriceLevel(price_level),
                limit=limit,
                sort_by="quality",
                sort_order="desc"
            )
            
            response = self.search_places(search_query)
            return response.places
            
        except Exception as e:
            logger.error(f"Error getting places by price level {price_level}: {e}")
            return []
    
    def get_popular_places(self, limit: int = 20) -> List[Place]:
        """Get most popular places."""
        try:
            search_query = PlaceSearch(
                limit=limit,
                sort_by="popularity",
                sort_order="desc"
            )
            
            response = self.search_places(search_query)
            return response.places
            
        except Exception as e:
            logger.error(f"Error getting popular places: {e}")
            return []
    
    def get_high_quality_places(self, limit: int = 20) -> List[Place]:
        """Get places with high quality scores."""
        try:
            search_query = PlaceSearch(
                limit=limit,
                sort_by="quality",
                sort_order="desc"
            )
            
            response = self.search_places(search_query)
            return response.places
            
        except Exception as e:
            logger.error(f"Error getting high quality places: {e}")
            return []
    
    def get_recent_places(self, limit: int = 20) -> List[Place]:
        """Get recently added/updated places."""
        try:
            search_query = PlaceSearch(
                limit=limit,
                sort_by="updated_at",
                sort_order="desc"
            )
            
            response = self.search_places(search_query)
            return response.places
            
        except Exception as e:
            logger.error(f"Error getting recent places: {e}")
            return []
    
    def get_places_stats(self) -> Dict[str, Any]:
        """Get places statistics."""
        try:
            return self.db.get_places_stats()
        except Exception as e:
            logger.error(f"Error getting places stats: {e}")
            return {}
    
    def rebuild_search_index(self) -> bool:
        """Rebuild FTS5 search index."""
        try:
            logger.info("Rebuilding search index...")
            success = self.db.rebuild_fts_index()
            
            if success:
                logger.info("Search index rebuilt successfully")
            else:
                logger.error("Failed to rebuild search index")
            
            return success
            
        except Exception as e:
            logger.error(f"Error rebuilding search index: {e}")
            return False
    
    def get_all_places(self, limit: int = 1000) -> List[Place]:
        """Get all places (for debugging/testing)."""
        try:
            search_query = PlaceSearch(
                limit=limit,
                sort_by="updated_at",
                sort_order="desc"
            )
            
            response = self.search_places(search_query)
            return response.places
            
        except Exception as e:
            logger.error(f"Error getting all places: {e}")
            return []
    
    def close(self):
        """Close service and database connections."""
        try:
            self.db.close()
            logger.info("Places service closed")
        except Exception as e:
            logger.error(f"Error closing places service: {e}")


# Фабрика для создания сервиса
def create_places_service(db_path: str = "data/processed/places.db") -> PlacesService:
    """Create and return a places service instance."""
    return PlacesService(db_path)
