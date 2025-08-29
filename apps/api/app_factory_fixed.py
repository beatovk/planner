"""
Fixed app factory with real database integration.
"""

import os
import json
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from packages.wp_places.api import places_router
from packages.wp_core.config import settings
from packages.wp_core.db import get_engine
from packages.wp_cache.cache import CacheClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print("Starting application...")
    
    # 1) Database Engine
    try:
        db_engine = get_engine()
        app.state.db_engine = db_engine
        if db_engine:
            print("✅ Database engine initialized")
        else:
            print("⚠️ Database engine initialization failed")
    except Exception as e:
        print(f"❌ Database engine initialization failed: {e}")
        app.state.db_engine = None
    
    # 2) Redis Client - REMOVED
    # Redis dependencies removed - using simple in-memory cache
    app.state.redis = None
    print("ℹ️ Redis removed - using simple in-memory cache")
    
    # 3) Cache Client
    try:
        cache_client = CacheClient(default_ttl=settings.CACHE_TTL)
        app.state.cache = cache_client
        print("✅ Cache client initialized")
    except Exception as e:
        print(f"❌ Cache client initialization failed: {e}")
        app.state.cache = None
    
    # 4) Health check
    try:
        if app.state.db_engine:
            with app.state.db_engine.connect() as conn:
                conn.execute("SELECT 1")
            print("✅ Database health check passed")
    except Exception as e:
        print(f"⚠️ Database health check failed: {e}")
    
    yield
    
    # --- Shutdown ---
    print("Shutting down application...")
    
    # 1) Cache (simple in-memory)
    if getattr(app.state, "cache", None):
        try:
            if hasattr(app.state.cache, 'close'):
                await app.state.cache.close()
            print("✅ Cache client closed")
        except Exception as e:
            print(f"⚠️ Cache shutdown error: {e}")
    
    # 2) DB Engine
    if getattr(app.state, "db_engine", None):
        try:
            app.state.db_engine.dispose()
            print("✅ Database engine disposed")
        except Exception as e:
            print(f"⚠️ Database engine disposal error: {e}")
    
    print("✅ All resources cleaned up")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files
    static_dir = Path(__file__).parent.parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        print(f"Static files directory: {static_dir}")
    
    # Include routers
    app.include_router(places_router)
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Week Planner API",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/health"
        }
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        try:
            # Check database
            db_healthy = False
            if app.state.db_engine:
                try:
                    with app.state.db_engine.connect() as conn:
                        conn.execute("SELECT 1")
                    db_healthy = True
                except Exception:
                    pass
            
            # Check cache
            cache_healthy = app.state.cache is not None
            
            return {
                "status": "healthy",
                "timestamp": "2025-08-28T16:54:05.461061",
                "database": "healthy" if db_healthy else "unhealthy",
                "version": settings.APP_VERSION
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
    
    # Categories endpoint
    @app.get("/api/categories")
    async def get_categories():
        """Get available place categories."""
        try:
            categories = [
                {"id": "food_dining", "name": "Food & Dining", "description": "Restaurants, cafes, and food experiences"},
                {"id": "entertainment", "name": "Entertainment", "description": "Bars, clubs, and entertainment venues"},
                {"id": "wellness", "name": "Wellness", "description": "Spas, yoga, and wellness activities"},
                {"id": "art_exhibits", "name": "Art & Culture", "description": "Museums, galleries, and cultural sites"},
                {"id": "shopping", "name": "Shopping", "description": "Markets, malls, and shopping areas"},
                {"id": "rooftop", "name": "Rooftop", "description": "Rooftop bars and restaurants with views"}
            ]
            return {"categories": categories}
            
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

    @app.post("/api/analyze-query")
    async def api_analyze_query(request: Dict[str, Any]):
        """Поиск мест по запросу"""
        try:
            from fastapi import HTTPException
            
            # Получаем запрос
            user_query = request.get('query', '')
            if not user_query:
                raise HTTPException(status_code=400, detail="Query is required")
            
            # Используем PlacesService для получения реальных данных из базы
            from packages.wp_places.service import PlacesService
            
            places_service = PlacesService()
            city = "Bangkok"  # По умолчанию ищем в Бангкоке
            
            # Получаем все места из базы данных
            all_places = places_service.get_places_by_flags(city, [], 100)  # Без фильтра по флагам
            
            # Простой поиск по ключевым словам
            query_lower = user_query.lower()
            matched_places = []
            
            for place in all_places:
                score = 0
                
                # Проверяем название
                if any(word in place.name.lower() for word in query_lower.split()):
                    score += 10
                
                # Проверяем описание
                if place.description:
                    if any(word in place.description.lower() for word in query_lower.split()):
                        score += 5
                
                # Проверяем теги
                if place.tags:
                    for tag in place.tags:
                        if any(word in tag.lower() for word in query_lower.split()):
                            score += 8
                
                # Проверяем флаги
                if place.flags:
                    for flag in place.flags:
                        if any(word in flag.lower() for word in query_lower.split()):
                            score += 6
                
                # Специальные правила для категорий
                if any(word in query_lower for word in ['еда', 'есть', 'ресторан', 'кафе', 'кухня', 'food', 'eat', 'restaurant', 'cafe', 'dining']):
                    if any(flag in place.flags for flag in ['food_dining', 'thai_cuisine', 'cafes']):
                        score += 15
                    if any(tag in place.tags for tag in ['food', 'restaurant', 'cafe']):
                        score += 10
                
                if any(word in query_lower for word in ['парк', 'природа', 'прогулка', 'park', 'nature', 'outdoor', 'walk']):
                    if any(flag in place.flags for flag in ['parks', 'nature']):
                        score += 15
                    if any(tag in place.tags for tag in ['park', 'nature']):
                        score += 10
                
                if any(word in query_lower for word in ['искусство', 'музей', 'галерея', 'art', 'museum', 'gallery', 'exhibition']):
                    if any(flag in place.flags for flag in ['art_exhibits', 'culture']):
                        score += 15
                    if any(tag in place.tags for tag in ['art', 'museum', 'gallery']):
                        score += 10
                
                if any(word in query_lower for word in ['развлечения', 'музыка', 'клуб', 'entertainment', 'music', 'club', 'jazz', 'electronic']):
                    if any(flag in place.flags for flag in ['entertainment', 'jazz', 'electronic']):
                        score += 15
                    if any(tag in place.tags for tag in ['jazz', 'live music', 'electronic', 'club']):
                        score += 10
                
                if any(word in query_lower for word in ['спа', 'массаж', 'йога', 'wellness', 'spa', 'massage', 'yoga']):
                    if any(flag in place.flags for flag in ['wellness', 'traditional', 'fitness']):
                        score += 15
                    if any(tag in place.tags for tag in ['wellness', 'spa', 'massage', 'yoga']):
                        score += 10
                
                if any(word in query_lower for word in ['крыша', 'вид', 'rooftop', 'view', 'sky']):
                    if any(flag in place.flags for flag in ['rooftop']):
                        score += 15
                    if any(tag in place.tags for tag in ['rooftop', 'view']):
                        score += 10
                
                # Если место подходит, добавляем его
                if score > 0:
                    place._relevance_score = score
                    matched_places.append(place)
            
            # Сортируем по релевантности
            matched_places.sort(key=lambda x: getattr(x, '_relevance_score', 0), reverse=True)
            top_places = matched_places[:20]  # Топ-20 мест
            
            # Конвертируем в формат для API
            places_data = []
            for place in top_places:
                place_dict = {
                    'id': place.id,
                    'name': place.name,
                    'description': place.description,
                    'city': place.city,
                    'address': place.address,
                    'tags': place.tags,
                    'flags': place.flags,
                    'rating': place.rating,
                    'price_range': place.price_range,
                    'google_maps_url': place.google_maps_url,
                    'source': place.source
                }
                places_data.append(place_dict)
            
            return {
                "success": True,
                "query": user_query,
                "city": city,
                "total": len(places_data),
                "places": places_data
            }
                
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=f"Query analysis failed: {str(e)}")
    
    return app
