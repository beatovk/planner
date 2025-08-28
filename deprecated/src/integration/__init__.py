"""
Integration module - Combines dedup, quality, and search/cache components
"""

from .places_pipeline import (
    PlacesPipeline,
    PipelineResult,
    create_places_pipeline
)

__all__ = [
    'PlacesPipeline',
    'PipelineResult', 
    'create_places_pipeline'
]
