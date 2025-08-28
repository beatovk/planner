"""
Places API routes registration.

This module provides the register_places_routes function to register
all places-related endpoints with a FastAPI application.
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .service import PlacesService
from ..wp_cache.redis_safe import should_bypass_redis, get_redis_status

log = logging.getLogger(__name__)


def register_places_routes(app: FastAPI) -> None:
    """Register all places-related routes with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.get("/api/places")
    def api_places(
        city: str = "bangkok",
        flags: str = "",
        limit: int = 50
    ):
        """
        Get places by city and flags.
        
        Args:
            city: City name (default: bangkok)
            flags: Comma-separated flags (e.g., "food_dining,art_exhibits")
            limit: Maximum number of places to return
        """
        try:
            # Check Redis status for headers
            redis_bypass = should_bypass_redis()
            redis_status = get_redis_status()
            
            # Debug Redis status
            log.info(f"Redis bypass: {redis_bypass}")
            log.info(f"Redis status: {redis_status}")
            
            service = PlacesService()
            flag_list = [f.strip() for f in flags.split(",") if f.strip()] if flags else []
            
            # Track cache status
            cache_status = "BYPASS" if redis_bypass else "MISS"
            source = "db"  # Default to database
            
            if flag_list:
                places = service.get_places_by_flags(city, flag_list, limit)
                # Check if places came from cache
                if places and hasattr(places[0], '_from_cache') and places[0]._from_cache:
                    cache_status = "HIT"
                    source = "cache"
            else:
                places = service.get_all_places(city, limit)
            
            # Convert places to dict for JSON serialization
            places_data = []
            for place in places:
                place_dict = place.to_dict()
                # Remove internal fields
                place_dict.pop("created_at", None)
                place_dict.pop("updated_at", None)
                places_data.append(place_dict)
            
            # Set response headers
            response = JSONResponse({
                "city": city,
                "flags": flag_list,
                "places": places_data,
                "total": len(places_data)
            })
            
            # Add cache status headers
            response.headers["X-Cache-Status"] = cache_status
            response.headers["X-Source"] = source
            
            # Add Redis circuit breaker status
            if "circuit_breaker" in redis_status:
                circuit_state = redis_status["circuit_breaker"]["state"]
                response.headers["X-Redis-Circuit"] = circuit_state
            
            # Add Redis bypass info
            if redis_bypass:
                response.headers["X-Redis-Bypass"] = "true"
                if redis_status.get("cache_disabled"):
                    response.headers["X-Redis-Bypass-Reason"] = "WP_CACHE_DISABLE=1"
                elif redis_status.get("circuit_breaker", {}).get("state") == "OPEN":
                    response.headers["X-Redis-Bypass-Reason"] = "circuit_open"
            
            return response
            
        except Exception as e:
            log.error(f"Error getting places: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get places: {str(e)}")

    @app.get("/api/places/categories")
    def api_places_categories():
        """Get available place categories/flags."""
        try:
            service = PlacesService()
            categories = service.fetcher.get_supported_categories()
            
            return {
                "categories": categories,
                "description": "Available place categories for filtering"
            }
            
        except Exception as e:
            log.error(f"Error getting place categories: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get place categories: {str(e)}")

    @app.get("/api/places/stats")
    def api_places_stats(city: str = "bangkok"):
        """Get places statistics for a city."""
        try:
            service = PlacesService()
            stats = service.get_stats(city)
            
            return stats
            
        except Exception as e:
            log.error(f"Error getting places stats: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get places stats: {str(e)}")

    @app.post("/api/places/warm-cache")
    async def api_places_warm_cache(city: str = "bangkok", flags: str = ""):
        """Warm up places cache for specified flags."""
        try:
            service = PlacesService()
            flag_list = [f.strip() for f in flags.split(",") if f.strip()] if flags else None
            
            if flag_list:
                # Warm specific flags
                for flag in flag_list:
                    service.warm_cache_for_flag(city, flag)
                message = f"Warmed cache for flags: {', '.join(flag_list)}"
            else:
                # Warm all categories
                service.warm_cache_all_categories(city)
                message = "Warmed cache for all categories"
            
            return {
                "message": message,
                "city": city,
                "flags": flag_list or "all"
            }
            
        except Exception as e:
            log.error(f"Error warming places cache: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to warm cache: {str(e)}")
