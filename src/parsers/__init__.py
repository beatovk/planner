"""
Parsers package for Bangkok Places Parser.
"""

from .recipe_engine import RecipeEngine, SourceRecipe, create_recipe_engine
from .extractors import (
    BaseExtractor,
    JSONLDExtractor,
    OpenGraphExtractor,
    CSSExtractor,
    UniversalExtractor,
    create_extractor
)
from .extractor_engine import ExtractorEngine, ContentType, create_extractor_engine
from .fallback_engine import FallbackEngine, create_fallback_engine
from .content_detector import ContentTypeDetector, detect_content_type, get_detailed_analysis

__all__ = [
    'RecipeEngine',
    'SourceRecipe',
    'create_recipe_engine',
    'BaseExtractor',
    'JSONLDExtractor',
    'OpenGraphExtractor',
    'CSSExtractor',
    'UniversalExtractor',
    'create_extractor',
    'ExtractorEngine',
    'ContentType',
    'create_extractor_engine',
    'FallbackEngine',
    'create_fallback_engine',
    'ContentTypeDetector',
    'detect_content_type',
    'get_detailed_analysis'
]
