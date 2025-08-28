#!/usr/bin/env python3
"""
Integrated API - Combines all pipeline components with REST API endpoints
Provides unified interface for places processing, search, and management.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Добавляем src в Python path
sys.path.insert(0, str(Path('.') / 'src'))

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from integration import create_places_pipeline, PlacesPipeline, PipelineResult
from cache import CacheConfig


# Pydantic models for API requests/responses
class PlaceData(BaseModel):
    """Place data model for API requests."""
    id: str
    name: str
    city: str
    domain: str
    url: str
    description: Optional[str] = None
    address: Optional[str] = None
    geo_lat: Optional[float] = None
    geo_lng: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[str] = None
    price_level: Optional[str] = None
    rating: Optional[float] = None
    photos: List[Dict[str, Any]] = Field(default_factory=list)
    image_url: Optional[str] = None
    quality_score: Optional[float] = None
    last_updated: Optional[str] = None


class PlaceProcessingRequest(BaseModel):
    """Request model for processing places."""
    places: List[PlaceData]
    min_quality_score: float = Field(default=0.7, ge=0.0, le=1.0)
    require_photos: bool = Field(default=True)


class PlaceProcessingResponse(BaseModel):
    """Response model for place processing."""
    total_places: int
    new_places: int
    duplicates: int
    rejected: int
    errors: int
    processing_time: float
    results: List[Dict[str, Any]]


class SearchRequest(BaseModel):
    """Request model for searching places."""
    query: str
    city: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchResponse(BaseModel):
    """Response model for search results."""
    query: str
    total_results: int
    results: List[Dict[str, Any]]


class CacheWarmingRequest(BaseModel):
    """Request model for cache warming."""
    cities: List[str] = Field(default_factory=lambda: ['Bangkok'])
    flags: List[str] = Field(default_factory=lambda: ['attractions', 'shopping', 'food_dining'])


class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    status: str
    timestamp: str
    components: Dict[str, str]
    statistics: Dict[str, Any]


class IntegratedPlacesAPI:
    """Integrated API combining all pipeline components."""
    
    def __init__(self, 
                 db_path: str = "data/integrated_places.db",
                 redis_config: Optional[CacheConfig] = None,
                 min_quality_score: float = 0.7,
                 require_photos: bool = True):
        """
        Initialize the integrated API.
        
        Args:
            db_path: Path to SQLite database
            redis_config: Redis configuration
            min_quality_score: Minimum quality score for acceptance
            require_photos: Whether photos are required
        """
        self.db_path = db_path
        self.redis_config = redis_config
        self.min_quality_score = min_quality_score
        self.require_photos = require_photos
        
        # Setup logging first
        self._setup_logging()
        
        # Initialize pipeline
        self.pipeline = None
        self._initialize_pipeline()
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Integrated Places API",
            description="Unified API for places processing, deduplication, quality assessment, and search",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Register routes
        self._register_routes()
    
    def _setup_logging(self):
        """Setup logging for the API."""
        self.logger = logging.getLogger('IntegratedPlacesAPI')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _initialize_pipeline(self):
        """Initialize the places pipeline."""
        try:
            self.pipeline = create_places_pipeline(
                db_path=self.db_path,
                redis_config=self.redis_config,
                min_quality_score=self.min_quality_score,
                require_photos=self.require_photos
            )
            self.logger.info("✓ Pipeline initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize pipeline: {e}")
            raise
    
    def _register_routes(self):
        """Register all API routes."""
        
        @self.app.post("/api/places/process", response_model=PlaceProcessingResponse)
        async def process_places(request: PlaceProcessingRequest):
            """Process a batch of places through the complete pipeline."""
            try:
                start_time = datetime.now()
                
                # Convert Pydantic models to dictionaries
                places_data = [place.dict() for place in request.places]
                
                # Process places through pipeline
                results = self.pipeline.process_batch(places_data)
                
                # Convert results to response format
                response_results = []
                for result in results:
                    response_results.append({
                        'place_id': result.place_id,
                        'name': result.name,
                        'city': result.city,
                        'status': result.status,
                        'dedup_info': result.dedup_info,
                        'quality_metrics': result.quality_metrics.get_overall_score() if result.quality_metrics else None,
                        'search_indexed': result.search_indexed,
                        'cache_updated': result.cache_updated,
                        'processing_time': result.processing_time,
                        'errors': result.errors
                    })
                
                # Get pipeline statistics
                stats = self.pipeline.get_statistics()
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                return PlaceProcessingResponse(
                    total_places=len(results),
                    new_places=stats['new_places'],
                    duplicates=stats['duplicates'],
                    rejected=stats['rejected'],
                    errors=stats['errors'],
                    processing_time=processing_time,
                    results=response_results
                )
                
            except Exception as e:
                self.logger.error(f"Error processing places: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/places/process/async", response_model=Dict[str, str])
        async def process_places_async(request: PlaceProcessingRequest, background_tasks: BackgroundTasks):
            """Process places asynchronously in the background."""
            try:
                # Add task to background processing
                background_tasks.add_task(self._process_places_background, request.places)
                
                return {
                    "message": "Places processing started in background",
                    "total_places": len(request.places),
                    "task_id": f"task_{datetime.now().timestamp()}"
                }
                
            except Exception as e:
                self.logger.error(f"Error starting async processing: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/places/search", response_model=SearchResponse)
        async def search_places(
            query: str,
            city: Optional[str] = None,
            limit: int = 50,
            offset: int = 0
        ):
            """Search places using FTS5."""
            try:
                if not self.pipeline or not self.pipeline.search_engine:
                    raise HTTPException(status_code=500, detail="Search engine not available")
                
                # Perform search
                results = self.pipeline.search_engine.search_places(query, city, limit, offset)
                
                # Convert to response format
                search_results = []
                for result in results:
                    search_results.append({
                        'place_id': result.place_id,
                        'name': result.name,
                        'city': result.city,
                        'domain': result.raw_data.get('domain'),
                        'address': result.address,
                        'geo_lat': result.raw_data.get('geo_lat'),
                        'geo_lng': result.raw_data.get('geo_lng'),
                        'tags': result.tags,
                        'flags': result.flags,
                        'relevance_score': result.relevance_score,
                        'quality_score': result.raw_data.get('quality_score'),
                        'rating': result.raw_data.get('rating'),
                        'image_url': result.raw_data.get('image_url')
                    })
                
                return SearchResponse(
                    query=query,
                    total_results=len(search_results),
                    results=search_results
                )
                
            except Exception as e:
                self.logger.error(f"Error searching places: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/places/flags/{city}/{flag}")
        async def get_places_by_flag(city: str, flag: str, limit: int = 50):
            """Get places by flag."""
            try:
                if not self.pipeline or not self.pipeline.search_engine:
                    raise HTTPException(status_code=500, detail="Search engine not available")
                
                # Search by flag
                results = self.pipeline.search_engine.search_by_flags([flag], city, limit)
                
                # Convert to response format
                places = []
                for result in results:
                    places.append({
                        'place_id': result.place_id,
                        'name': result.name,
                        'city': result.city,
                        'domain': result.raw_data.get('domain'),
                        'address': result.address,
                        'tags': result.tags,
                        'flags': result.flags,
                        'quality_score': result.raw_data.get('quality_score'),
                        'rating': result.raw_data.get('rating'),
                        'image_url': result.raw_data.get('image_url')
                    })
                
                return {
                    'city': city,
                    'flag': flag,
                    'total_places': len(places),
                    'places': places
                }
                
            except Exception as e:
                self.logger.error(f"Error getting places by flag: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/places/recommend")
        async def get_recommendations(city: str, limit: int = 10):
            """Get place recommendations."""
            try:
                if not self.pipeline or not self.pipeline.search_engine:
                    raise HTTPException(status_code=500, detail="Search engine not available")
                
                # Get recommendations
                recommendations = self.pipeline.search_engine.get_recommendations(city, limit)
                
                # Convert to response format
                recs = []
                for rec in recommendations:
                    recs.append({
                        'place_id': rec.place_id,
                        'name': rec.name,
                        'city': rec.city,
                        'domain': rec.raw_data.get('domain'),
                        'tags': rec.tags,
                        'flags': rec.flags,
                        'quality_score': rec.raw_data.get('quality_score'),
                        'rating': rec.raw_data.get('rating'),
                        'image_url': rec.raw_data.get('image_url')
                    })
                
                return {
                    'city': city,
                    'total_recommendations': len(recs),
                    'recommendations': recs
                }
                
            except Exception as e:
                self.logger.error(f"Error getting recommendations: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/places/cache/warm")
        async def warm_cache(request: CacheWarmingRequest):
            """Warm up the cache with popular data."""
            try:
                if not self.pipeline or not self.pipeline.cache_engine:
                    raise HTTPException(status_code=500, detail="Cache engine not available")
                
                # Warm cache
                self.pipeline.warm_cache(request.cities, request.flags)
                
                return {
                    "message": "Cache warming completed",
                    "cities": request.cities,
                    "flags": request.flags
                }
                
            except Exception as e:
                self.logger.error(f"Error warming cache: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/places/system/optimize")
        async def optimize_system():
            """Optimize all system components."""
            try:
                if not self.pipeline:
                    raise HTTPException(status_code=500, detail="Pipeline not available")
                
                # Optimize system
                self.pipeline.optimize_system()
                
                return {"message": "System optimization completed"}
                
            except Exception as e:
                self.logger.error(f"Error optimizing system: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/places/system/status", response_model=SystemStatusResponse)
        async def get_system_status():
            """Get system status and statistics."""
            try:
                if not self.pipeline:
                    raise HTTPException(status_code=500, detail="Pipeline not available")
                
                # Get pipeline statistics
                stats = self.pipeline.get_statistics()
                
                # Component status
                components = {
                    'dedup_engine': 'available' if self.pipeline.dedup_engine else 'unavailable',
                    'quality_engine': 'available' if self.pipeline.quality_engine else 'unavailable',
                    'search_engine': 'available' if self.pipeline.search_engine else 'unavailable',
                    'cache_engine': 'available' if self.pipeline.cache_engine else 'unavailable'
                }
                
                return SystemStatusResponse(
                    status='healthy' if all(c == 'available' for c in components.values()) else 'degraded',
                    timestamp=datetime.now().isoformat(),
                    components=components,
                    statistics=stats
                )
                
            except Exception as e:
                self.logger.error(f"Error getting system status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            try:
                if not self.pipeline:
                    return {"status": "unhealthy", "error": "Pipeline not available"}
                
                # Check component availability
                components_ok = (
                    self.pipeline.dedup_engine is not None and
                    self.pipeline.quality_engine is not None and
                    self.pipeline.search_engine is not None
                )
                
                if components_ok:
                    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
                else:
                    return {"status": "degraded", "timestamp": datetime.now().isoformat()}
                    
            except Exception as e:
                return {"status": "unhealthy", "error": str(e)}
    
    def _process_places_background(self, places: List[PlaceData]):
        """Process places in the background."""
        try:
            self.logger.info(f"Starting background processing of {len(places)} places")
            
            # Convert to dictionaries and process
            places_data = [place.dict() for place in places]
            results = self.pipeline.process_batch(places_data)
            
            self.logger.info(f"Background processing completed: {len(results)} places processed")
            
        except Exception as e:
            self.logger.error(f"Background processing failed: {e}")
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.app
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """Run the API server."""
        uvicorn.run(self.app, host=host, port=port, **kwargs)
    
    def close(self):
        """Close the API and pipeline."""
        try:
            if self.pipeline:
                self.pipeline.close()
            self.logger.info("✓ API closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing API: {e}")


def create_integrated_api(db_path: str = "data/integrated_places.db",
                         redis_config: Optional[CacheConfig] = None,
                         min_quality_score: float = 0.7,
                         require_photos: bool = True) -> IntegratedPlacesAPI:
    """
    Factory function to create an IntegratedPlacesAPI instance.
    
    Args:
        db_path: Path to SQLite database
        redis_config: Redis configuration
        min_quality_score: Minimum quality score for acceptance
        require_photos: Whether photos are required
        
    Returns:
        Configured IntegratedPlacesAPI instance
    """
    return IntegratedPlacesAPI(
        db_path=db_path,
        redis_config=redis_config,
        min_quality_score=min_quality_score,
        require_photos=require_photos
    )
