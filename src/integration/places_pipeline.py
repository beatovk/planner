#!/usr/bin/env python3
"""
Places Pipeline - Integrated system combining dedup, quality, and search/cache
Integrates all components from Steps 6, 7, and 8 into a unified pipeline.
"""

import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

# Добавляем src в Python path
sys.path.insert(0, str(Path('.') / 'src'))

from dedup import create_dedup_engine, DedupEngine
from quality import create_quality_engine, QualityEngine, QualityMetrics
from search import create_fts5_engine, FTS5Engine
from cache import create_redis_cache_engine, RedisCacheEngine, CacheConfig


@dataclass
class PipelineResult:
    """Result of the places pipeline processing."""
    place_id: str
    name: str
    city: str
    status: str  # 'new', 'duplicate', 'rejected', 'updated'
    dedup_info: Optional[Dict[str, Any]] = None
    quality_metrics: Optional[QualityMetrics] = None
    search_indexed: bool = False
    cache_updated: bool = False
    processing_time: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class PlacesPipeline:
    """Integrated pipeline for processing places through dedup, quality, and search/cache."""
    
    def __init__(self, 
                 db_path: str = "data/integrated_places.db",
                 redis_config: Optional[CacheConfig] = None,
                 min_quality_score: float = 0.7,
                 require_photos: bool = True):
        """
        Initialize the integrated places pipeline.
        
        Args:
            db_path: Path to SQLite database
            redis_config: Redis configuration (optional)
            min_quality_score: Minimum quality score for acceptance
            require_photos: Whether photos are required
        """
        self.db_path = db_path
        self.min_quality_score = min_quality_score
        self.require_photos = require_photos
        
        # Initialize components
        self.dedup_engine = None
        self.quality_engine = None
        self.search_engine = None
        self.cache_engine = None
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'new_places': 0,
            'duplicates': 0,
            'rejected': 0,
            'updated': 0,
            'search_indexed': 0,
            'cache_updated': 0,
            'errors': 0,
            'processing_time': 0.0
        }
        
        # Initialize logging
        self._setup_logging()
        
        # Initialize all components
        self._initialize_components(redis_config)
    
    def _setup_logging(self):
        """Setup logging for the pipeline."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/places_pipeline.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('PlacesPipeline')
        
        # Create logs directory if it doesn't exist
        Path('logs').mkdir(exist_ok=True)
    
    def _initialize_components(self, redis_config: Optional[CacheConfig]):
        """Initialize all pipeline components."""
        try:
            self.logger.info("Initializing pipeline components...")
            
            # 1. Dedup Engine
            self.logger.info("Initializing dedup engine...")
            self.dedup_engine = create_dedup_engine()
            self.logger.info("✓ Dedup engine initialized")
            
            # 2. Quality Engine
            self.logger.info("Initializing quality engine...")
            self.quality_engine = create_quality_engine(
                min_completeness=self.min_quality_score,
                require_photo=self.require_photos
            )
            self.logger.info("✓ Quality engine initialized")
            
            # 3. Search Engine (FTS5)
            self.logger.info("Initializing FTS5 search engine...")
            self.search_engine = create_fts5_engine(self.db_path)
            self.logger.info("✓ FTS5 search engine initialized")
            
            # 4. Cache Engine (Redis)
            if redis_config:
                self.logger.info("Initializing Redis cache engine...")
                self.cache_engine = create_redis_cache_engine(redis_config)
                if self.cache_engine._is_connected():
                    self.logger.info("✓ Redis cache engine initialized")
                else:
                    self.logger.warning("⚠️ Redis cache engine not available")
                    self.cache_engine = None
            else:
                self.logger.info("No Redis config provided, skipping cache")
            
            self.logger.info("✓ All pipeline components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    def process_place(self, place_data: Dict[str, Any]) -> PipelineResult:
        """
        Process a single place through the complete pipeline.
        
        Args:
            place_data: Place data dictionary
            
        Returns:
            PipelineResult with processing status and details
        """
        start_time = time.time()
        place_id = place_data.get('id', 'unknown')
        
        try:
            self.logger.info(f"Processing place: {place_data.get('name', 'Unknown')} (ID: {place_id})")
            
            # Step 1: Deduplication
            dedup_result = self._process_dedup(place_data)
            if dedup_result['is_duplicate']:
                processing_time = time.time() - start_time
                return PipelineResult(
                    place_id=place_id,
                    name=place_data.get('name', 'Unknown'),
                    city=place_data.get('city', 'Unknown'),
                    status='duplicate',
                    dedup_info=dedup_result,
                    processing_time=processing_time
                )
            
            # Step 2: Quality Assessment
            quality_result = self._process_quality(place_data)
            if not quality_result['accepted']:
                processing_time = time.time() - start_time
                return PipelineResult(
                    place_id=place_id,
                    name=place_data.get('name', 'Unknown'),
                    city=place_data.get('city', 'Unknown'),
                    status='rejected',
                    quality_metrics=quality_result['metrics'],
                    processing_time=processing_time,
                    errors=quality_result['reasons']
                )
            
            # Step 3: Search Indexing
            search_result = self._process_search_indexing(place_data)
            
            # Step 4: Cache Update
            cache_result = self._process_cache_update(place_data)
            
            # Update statistics
            self._update_stats('new_places')
            if search_result:
                self._update_stats('search_indexed')
            if cache_result:
                self._update_stats('cache_updated')
            
            processing_time = time.time() - start_time
            self._update_stats('processing_time', processing_time)
            
            self.logger.info(f"✓ Place processed successfully: {place_data.get('name', 'Unknown')}")
            
            return PipelineResult(
                place_id=place_id,
                name=place_data.get('name', 'Unknown'),
                city=place_data.get('city', 'Unknown'),
                status='new',
                dedup_info=dedup_result,
                quality_metrics=quality_result['metrics'],
                search_indexed=search_result,
                cache_updated=cache_result,
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"Error processing place {place_id}: {e}")
            self._update_stats('errors')
            
            processing_time = time.time() - start_time
            return PipelineResult(
                place_id=place_id,
                name=place_data.get('name', 'Unknown'),
                city=place_data.get('city', 'Unknown'),
                status='error',
                processing_time=processing_time,
                errors=[str(e)]
            )
    
    def _process_dedup(self, place_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process deduplication for a place."""
        try:
            is_duplicate, duplicate_id = self.dedup_engine.add_place(place_data)
            
            return {
                'is_duplicate': is_duplicate,
                'duplicate_id': duplicate_id,
                'dedup_strategy': 'identity_key' if duplicate_id else None
            }
            
        except Exception as e:
            self.logger.error(f"Dedup processing error: {e}")
            return {'is_duplicate': False, 'duplicate_id': None, 'error': str(e)}
    
    def _process_quality(self, place_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process quality assessment for a place."""
        try:
            accepted, metrics, reasons = self.quality_engine.assess_place_quality(place_data)
            
            return {
                'accepted': accepted,
                'metrics': metrics,
                'reasons': reasons if not accepted else []
            }
            
        except Exception as e:
            self.logger.error(f"Quality assessment error: {e}")
            return {
                'accepted': False,
                'metrics': None,
                'reasons': [f"Quality assessment error: {e}"]
            }
    
    def _process_search_indexing(self, place_data: Dict[str, Any]) -> bool:
        """Process search indexing for a place."""
        try:
            if self.search_engine:
                success = self.search_engine.add_place(place_data)
                if success:
                    self.logger.debug(f"Place indexed in search: {place_data.get('name', 'Unknown')}")
                return success
            return False
            
        except Exception as e:
            self.logger.error(f"Search indexing error: {e}")
            return False
    
    def _process_cache_update(self, place_data: Dict[str, Any]) -> bool:
        """Process cache update for a place."""
        try:
            if self.cache_engine:
                city = place_data.get('city', 'unknown')
                flags = place_data.get('flags', [])
                
                # Cache by individual flags
                cache_success = True
                for flag in flags:
                    success = self.cache_engine.cache_places(city, [place_data], flag)
                    if not success:
                        cache_success = False
                
                if cache_success:
                    self.logger.debug(f"Place cached: {place_data.get('name', 'Unknown')}")
                
                return cache_success
            return False
            
        except Exception as e:
            self.logger.error(f"Cache update error: {e}")
            return False
    
    def _update_stats(self, stat_name: str, value: Any = 1):
        """Update pipeline statistics."""
        if stat_name in self.stats:
            if isinstance(self.stats[stat_name], (int, float)):
                if stat_name == 'processing_time':
                    self.stats[stat_name] += value
                else:
                    self.stats[stat_name] += value
            else:
                self.stats[stat_name] = value
    
    def process_batch(self, places_data: List[Dict[str, Any]]) -> List[PipelineResult]:
        """
        Process a batch of places through the pipeline.
        
        Args:
            places_data: List of place data dictionaries
            
        Returns:
            List of PipelineResult objects
        """
        self.logger.info(f"Processing batch of {len(places_data)} places...")
        
        results = []
        for place_data in places_data:
            result = self.process_place(place_data)
            results.append(result)
            
            # Update total processed count
            self._update_stats('total_processed')
        
        self.logger.info(f"Batch processing completed: {len(results)} places processed")
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        # Add component statistics
        stats = self.stats.copy()
        
        if self.dedup_engine:
            stats['dedup_stats'] = self.dedup_engine.get_statistics()
        
        if self.search_engine:
            stats['search_stats'] = self.search_engine.get_statistics()
        
        if self.cache_engine:
            stats['cache_stats'] = self.cache_engine.get_cache_statistics()
        
        # Calculate success rates
        if stats['total_processed'] > 0:
            stats['success_rate'] = (stats['new_places'] / stats['total_processed']) * 100
            stats['error_rate'] = (stats['errors'] / stats['total_processed']) * 100
            stats['avg_processing_time'] = stats['processing_time'] / stats['total_processed']
        
        return stats
    
    def warm_cache(self, cities: List[str] = None, flags: List[str] = None):
        """
        Warm up the cache with popular data.
        
        Args:
            cities: List of cities to warm cache for
            flags: List of flags to warm cache for
        """
        if not self.cache_engine:
            self.logger.warning("Cache engine not available, skipping cache warming")
            return
        
        try:
            self.logger.info("Starting cache warming...")
            
            if not cities:
                cities = ['Bangkok']  # Default city
            
            if not flags:
                flags = ['attractions', 'shopping', 'food_dining', 'cultural_heritage']
            
            for city in cities:
                for flag in flags:
                    try:
                        # Get places by flag from search engine
                        if self.search_engine:
                            places = self.search_engine.search_by_flags([flag], city, 20)
                            if places:
                                # Convert SearchResult to dict for caching
                                places_data = [place.raw_data for place in places]
                                success = self.cache_engine.cache_places(city, places_data, flag)
                                if success:
                                    self.logger.info(f"✓ Warmed cache for {city}:{flag} ({len(places_data)} places)")
                                else:
                                    self.logger.warning(f"⚠️ Failed to warm cache for {city}:{flag}")
                    except Exception as e:
                        self.logger.error(f"Error warming cache for {city}:{flag}: {e}")
            
            self.logger.info("Cache warming completed")
            
        except Exception as e:
            self.logger.error(f"Cache warming failed: {e}")
    
    def optimize_system(self):
        """Optimize all system components."""
        try:
            self.logger.info("Starting system optimization...")
            
            # Optimize search engine
            if self.search_engine:
                self.logger.info("Optimizing search engine...")
                self.search_engine.optimize_database()
                self.logger.info("✓ Search engine optimized")
            
            # Optimize cache
            if self.cache_engine:
                self.logger.info("Optimizing cache...")
                # Cache optimization is handled automatically by Redis
                self.logger.info("✓ Cache optimized")
            
            self.logger.info("System optimization completed")
            
        except Exception as e:
            self.logger.error(f"System optimization failed: {e}")
    
    def close(self):
        """Close all pipeline components."""
        try:
            self.logger.info("Closing pipeline components...")
            
            if self.search_engine:
                self.search_engine.close()
            
            if self.cache_engine:
                self.cache_engine.close()
            
            self.logger.info("✓ Pipeline components closed")
            
        except Exception as e:
            self.logger.error(f"Error closing pipeline: {e}")


def create_places_pipeline(db_path: str = "data/integrated_places.db",
                          redis_config: Optional[CacheConfig] = None,
                          min_quality_score: float = 0.7,
                          require_photos: bool = True) -> PlacesPipeline:
    """
    Factory function to create a PlacesPipeline instance.
    
    Args:
        db_path: Path to SQLite database
        redis_config: Redis configuration (optional)
        min_quality_score: Minimum quality score for acceptance
        require_photos: Whether photos are required
        
    Returns:
        Configured PlacesPipeline instance
    """
    return PlacesPipeline(
        db_path=db_path,
        redis_config=redis_config,
        min_quality_score=min_quality_score,
        require_photos=require_photos
    )
