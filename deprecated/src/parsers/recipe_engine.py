#!/usr/bin/env python3
"""
Recipe engine for managing source configurations.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SourceRecipe:
    """Source recipe configuration."""
    
    # Source information
    name: str
    domain: str
    base_url: str
    type: str
    language: str
    timezone: str
    
    # Extraction configuration
    extraction_priority: str
    jsonld_enabled: bool
    og_enabled: bool
    css_enabled: bool
    
    # JSON-LD selectors
    jsonld_selectors: Dict[str, str]
    
    # Open Graph selectors
    og_selectors: Dict[str, str]
    
    # CSS selectors
    css_selectors: Dict[str, str]
    
    # Navigation
    pagination_type: str
    next_page_selector: str
    max_pages: int
    categories: List[Dict[str, Any]]
    
    # Processing rules
    post_processing: Dict[str, Any]
    cleaning: Dict[str, bool]
    validation: Dict[str, Any]
    
    # Quality settings
    quality_scoring: Dict[str, int]
    min_quality_score: float
    filtering: Dict[str, Any]
    
    # Metadata
    version: str
    created_at: str
    updated_at: str
    author: str
    notes: str
    
    # Performance settings
    performance: Dict[str, Any]
    
    # Compliance settings
    compliance: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SourceRecipe':
        """Create SourceRecipe from dictionary."""
        source = data.get('source', {})
        extraction = data.get('extraction', {})
        navigation = data.get('navigation', {})
        processing = data.get('processing', {})
        quality = data.get('quality', {})
        metadata = data.get('metadata', {})
        
        return cls(
            # Source
            name=source.get('name', ''),
            domain=source.get('domain', ''),
            base_url=source.get('base_url', ''),
            type=source.get('type', 'website'),
            language=source.get('language', 'en'),
            timezone=source.get('timezone', 'Asia/Bangkok'),
            
            # Extraction
            extraction_priority=extraction.get('priority', 'css'),
            jsonld_enabled=extraction.get('jsonld', False),
            og_enabled=extraction.get('og', False),
            css_enabled=extraction.get('css', False),
            
            # Selectors
            jsonld_selectors=extraction.get('jsonld_selectors', {}),
            og_selectors=extraction.get('og_selectors', {}),
            css_selectors=extraction.get('css_selectors', {}),
            
            # Navigation
            pagination_type=navigation.get('pagination', {}).get('type', 'none'),
            next_page_selector=navigation.get('pagination', {}).get('next_page', ''),
            max_pages=navigation.get('pagination', {}).get('max_pages', 1),
            categories=navigation.get('categories', []),
            
            # Processing
            post_processing=processing.get('post_processing', {}),
            cleaning=processing.get('cleaning', {}),
            validation=processing.get('validation', {}),
            
            # Quality
            quality_scoring=quality.get('scoring', {}),
            min_quality_score=quality.get('scoring', {}).get('min_score', 0.5),
            filtering=quality.get('filtering', {}),
            
            # Metadata
            version=metadata.get('version', '1.0.0'),
            created_at=metadata.get('created_at', ''),
            updated_at=metadata.get('updated_at', ''),
            author=metadata.get('author', ''),
            notes=metadata.get('notes', ''),
            
            # Performance
            performance=metadata.get('performance', {}),
            
            # Compliance
            compliance=metadata.get('compliance', {})
        )
    
    def get_category_urls(self) -> List[Dict[str, Any]]:
        """Get all category URLs with their flags."""
        return [
            {
                'name': cat['name'],
                'url': cat['url'],
                'flags': cat.get('flags', []),
                'description': cat.get('description', '')
            }
            for cat in self.categories
        ]
    
    def get_flags_for_category(self, category_name: str) -> List[str]:
        """Get flags for a specific category."""
        for cat in self.categories:
            if cat['name'].lower() == category_name.lower():
                return cat.get('flags', [])
        return []
    
    def get_extraction_methods(self) -> List[str]:
        """Get list of enabled extraction methods in priority order."""
        methods = []
        
        if self.extraction_priority == 'jsonld':
            if self.jsonld_enabled:
                methods.append('jsonld')
            if self.og_enabled:
                methods.append('og')
            if self.css_enabled:
                methods.append('css')
        elif self.extraction_priority == 'og':
            if self.og_enabled:
                methods.append('og')
            if self.jsonld_enabled:
                methods.append('jsonld')
            if self.css_enabled:
                methods.append('css')
        else:  # css priority
            if self.css_enabled:
                methods.append('css')
            if self.jsonld_enabled:
                methods.append('jsonld')
            if self.og_enabled:
                methods.append('og')
        
        return methods
    
    def validate_recipe(self) -> List[str]:
        """Validate recipe configuration and return errors."""
        errors = []
        
        # Required fields
        if not self.name:
            errors.append("Source name is required")
        if not self.domain:
            errors.append("Domain is required")
        if not self.base_url:
            errors.append("Base URL is required")
        
        # At least one extraction method must be enabled
        if not any([self.jsonld_enabled, self.og_enabled, self.css_enabled]):
            errors.append("At least one extraction method must be enabled")
        
        # Categories must have required fields
        for i, cat in enumerate(self.categories):
            if not cat.get('name'):
                errors.append(f"Category {i+1} must have a name")
            if not cat.get('url'):
                errors.append(f"Category {i+1} must have a URL")
            if not cat.get('flags'):
                errors.append(f"Category {i+1} must have flags")
        
        # Quality score must be valid
        if not 0 <= self.min_quality_score <= 1:
            errors.append("Minimum quality score must be between 0 and 1")
        
        return errors


class RecipeEngine:
    """Engine for managing source recipes."""
    
    def __init__(self, recipes_dir: str = "config/sources"):
        """Initialize recipe engine."""
        self.recipes_dir = Path(recipes_dir)
        self.recipes: Dict[str, SourceRecipe] = {}
        self._load_recipes()
    
    def _load_recipes(self):
        """Load all recipe files from the recipes directory."""
        if not self.recipes_dir.exists():
            logger.warning(f"Recipes directory does not exist: {self.recipes_dir}")
            return
        
        for recipe_file in self.recipes_dir.glob("*.yaml"):
            try:
                with open(recipe_file, 'r', encoding='utf-8') as f:
                    recipe_data = yaml.safe_load(f)
                
                recipe = SourceRecipe.from_dict(recipe_data)
                
                # Validate recipe
                errors = recipe.validate_recipe()
                if errors:
                    logger.error(f"Recipe {recipe_file.name} has errors: {errors}")
                    continue
                
                # Store recipe by domain
                self.recipes[recipe.domain] = recipe
                logger.info(f"Loaded recipe: {recipe.name} ({recipe.domain})")
                
            except Exception as e:
                logger.error(f"Error loading recipe {recipe_file.name}: {e}")
    
    def get_recipe(self, domain: str) -> Optional[SourceRecipe]:
        """Get recipe for a specific domain."""
        return self.recipes.get(domain)
    
    def get_all_recipes(self) -> List[SourceRecipe]:
        """Get all loaded recipes."""
        return list(self.recipes.values())
    
    def get_recipe_by_name(self, name: str) -> Optional[SourceRecipe]:
        """Get recipe by source name."""
        for recipe in self.recipes.values():
            if recipe.name.lower() == name.lower():
                return recipe
        return None
    
    def reload_recipes(self):
        """Reload all recipes from disk."""
        logger.info("Reloading recipes...")
        self.recipes.clear()
        self._load_recipes()
        logger.info(f"Reloaded {len(self.recipes)} recipes")
    
    def add_recipe(self, recipe: SourceRecipe):
        """Add a new recipe."""
        self.recipes[recipe.domain] = recipe
        logger.info(f"Added recipe: {recipe.name} ({recipe.domain})")
    
    def remove_recipe(self, domain: str):
        """Remove a recipe."""
        if domain in self.recipes:
            recipe_name = self.recipes[domain].name
            del self.recipes[domain]
            logger.info(f"Removed recipe: {recipe_name} ({domain})")
    
    def get_supported_domains(self) -> List[str]:
        """Get list of supported domains."""
        return list(self.recipes.keys())
    
    def get_supported_categories(self) -> Dict[str, List[str]]:
        """Get supported categories by domain."""
        categories = {}
        for domain, recipe in self.recipes.items():
            categories[domain] = [cat['name'] for cat in recipe.categories]
        return categories
    
    def get_recipe_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded recipes."""
        stats = {
            'total_recipes': len(self.recipes),
            'domains': list(self.recipes.keys()),
            'total_categories': sum(len(recipe.categories) for recipe in self.recipes.values()),
            'extraction_methods': {},
            'quality_thresholds': {}
        }
        
        for domain, recipe in self.recipes.items():
            stats['extraction_methods'][domain] = recipe.get_extraction_methods()
            stats['quality_thresholds'][domain] = recipe.min_quality_score
        
        return stats
    
    def validate_all_recipes(self) -> Dict[str, List[str]]:
        """Validate all recipes and return errors by domain."""
        errors = {}
        for domain, recipe in self.recipes.items():
            recipe_errors = recipe.validate_recipe()
            if recipe_errors:
                errors[domain] = recipe_errors
        
        return errors
    
    def export_recipe(self, domain: str, output_path: str) -> bool:
        """Export a recipe to a file."""
        recipe = self.get_recipe(domain)
        if not recipe:
            logger.error(f"Recipe not found for domain: {domain}")
            return False
        
        try:
            # Convert recipe back to dictionary
            recipe_dict = {
                'source': {
                    'name': recipe.name,
                    'domain': recipe.domain,
                    'base_url': recipe.base_url,
                    'type': recipe.type,
                    'language': recipe.language,
                    'timezone': recipe.timezone
                },
                'extraction': {
                    'priority': recipe.extraction_priority,
                    'jsonld': recipe.jsonld_enabled,
                    'og': recipe.og_enabled,
                    'css': recipe.css_enabled,
                    'jsonld_selectors': recipe.jsonld_selectors,
                    'og_selectors': recipe.og_selectors,
                    'css_selectors': recipe.css_selectors
                },
                'navigation': {
                    'pagination': {
                        'type': recipe.pagination_type,
                        'next_page': recipe.next_page_selector,
                        'max_pages': recipe.max_pages
                    },
                    'categories': recipe.categories
                },
                'processing': {
                    'post_processing': recipe.post_processing,
                    'cleaning': recipe.cleaning,
                    'validation': recipe.validation
                },
                'quality': {
                    'scoring': recipe.quality_scoring,
                    'filtering': recipe.filtering
                },
                'metadata': {
                    'version': recipe.version,
                    'created_at': recipe.created_at,
                    'updated_at': recipe.updated_at,
                    'author': recipe.author,
                    'notes': recipe.notes,
                    'performance': recipe.performance,
                    'compliance': recipe.compliance
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(recipe_dict, f, default_flow_style=False, indent=2)
            
            logger.info(f"Exported recipe to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting recipe: {e}")
            return False


# Фабрика для создания движка рецептов
def create_recipe_engine(recipes_dir: str = "config/sources") -> RecipeEngine:
    """Create and return a recipe engine instance."""
    return RecipeEngine(recipes_dir)
