#!/usr/bin/env python3
"""
Universal normalizer that combines multiple normalization strategies.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from .base_normalizer import BaseNormalizer
from .bangkok_normalizer import BangkokNormalizer

logger = logging.getLogger(__name__)


class UniversalNormalizer:
    """Universal normalizer that combines multiple normalization strategies."""
    
    def __init__(self, enable_bangkok_normalization: bool = True):
        """Initialize universal normalizer."""
        self.base_normalizer = BaseNormalizer()
        self.bangkok_normalizer = BangkokNormalizer() if enable_bangkok_normalization else None
        
        # Normalization pipeline
        self.normalization_pipeline = self._build_pipeline()
        
        # Statistics
        self.normalization_stats = {
            'total_places_processed': 0,
            'total_fields_normalized': 0,
            'total_characters_removed': 0,
            'bangkok_areas_standardized': 0,
            'quality_improvements': []
        }
    
    def _build_pipeline(self) -> List[Dict[str, Any]]:
        """Build normalization pipeline."""
        pipeline = [
            {
                'name': 'base_cleaning',
                'description': 'Basic HTML cleaning and text normalization',
                'normalizer': self.base_normalizer,
                'enabled': True
            }
        ]
        
        if self.bangkok_normalizer:
            pipeline.append({
                'name': 'bangkok_specific',
                'description': 'Bangkok area standardization and local knowledge',
                'normalizer': self.bangkok_normalizer,
                'enabled': True
            })
        
        return pipeline
    
    def normalize_place(self, place: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a place using the full pipeline."""
        try:
            original_place = place.copy()
            normalized_place = place.copy()
            
            # Apply each normalization step
            for step in self.normalization_pipeline:
                if step['enabled']:
                    logger.debug(f"Applying {step['name']}: {step['description']}")
                    normalized_place = step['normalizer'].normalize_place(normalized_place)
            
            # Update statistics
            self._update_stats(original_place, normalized_place)
            
            # Add normalization metadata
            normalized_place['normalization_metadata'] = {
                'pipeline_steps': [step['name'] for step in self.normalization_pipeline if step['enabled']],
                'normalized_at': self.base_normalizer._get_timestamp(),
                'normalizer_version': '1.0'
            }
            
            return normalized_place
            
        except Exception as e:
            logger.error(f"Error in normalization pipeline: {e}")
            return place
    
    def normalize_places_batch(self, places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize multiple places in batch."""
        normalized_places = []
        
        for i, place in enumerate(places):
            try:
                logger.debug(f"Normalizing place {i+1}/{len(places)}")
                normalized_place = self.normalize_place(place)
                normalized_places.append(normalized_place)
            except Exception as e:
                logger.error(f"Error normalizing place {i+1}: {e}")
                normalized_places.append(place)  # Keep original if normalization fails
        
        return normalized_places
    
    def normalize_specific_field(self, field_name: str, value: Any, use_bangkok_knowledge: bool = True) -> Any:
        """Normalize a specific field."""
        try:
            if use_bangkok_knowledge and self.bangkok_normalizer:
                return self.bangkok_normalizer.normalize_specific_field(field_name, value)
            else:
                return self.base_normalizer.normalize_specific_field(field_name, value)
        except Exception as e:
            logger.error(f"Error normalizing field {field_name}: {e}")
            return value
    
    def get_normalization_stats(self) -> Dict[str, Any]:
        """Get comprehensive normalization statistics."""
        return {
            'pipeline_info': {
                'total_steps': len(self.normalization_pipeline),
                'enabled_steps': len([step for step in self.normalization_pipeline if step['enabled']]),
                'steps': [
                    {
                        'name': step['name'],
                        'description': step['description'],
                        'enabled': step['enabled']
                    }
                    for step in self.normalization_pipeline
                ]
            },
            'processing_stats': self.normalization_stats.copy(),
            'bangkok_knowledge': self._get_bangkok_knowledge_stats() if self.bangkok_normalizer else None
        }
    
    def _update_stats(self, original: Dict[str, Any], normalized: Dict[str, Any]):
        """Update normalization statistics."""
        self.normalization_stats['total_places_processed'] += 1
        
        # Get base normalization stats
        base_stats = self.base_normalizer.get_normalization_stats(original, normalized)
        
        # Update our stats
        self.normalization_stats['total_fields_normalized'] += base_stats['fields_normalized']
        self.normalization_stats['total_characters_removed'] += base_stats['characters_removed']
        
        # Add quality improvements
        self.normalization_stats['quality_improvements'].extend(base_stats['quality_improvements'])
        
        # Count Bangkok area standardizations
        if self.bangkok_normalizer and 'area' in original and 'area' in normalized:
            original_area = original['area']
            normalized_area = normalized['area']
            
            if original_area != normalized_area:
                # Check if this was a Bangkok area standardization
                if self.bangkok_normalizer.is_bangkok_area(original_area):
                    self.normalization_stats['bangkok_areas_standardized'] += 1
    
    def _get_bangkok_knowledge_stats(self) -> Dict[str, Any]:
        """Get Bangkok knowledge statistics."""
        if not self.bangkok_normalizer:
            return None
        
        return {
            'area_synonyms': self.bangkok_normalizer.get_bangkok_area_stats(),
            'total_abbreviations': len(self.bangkok_normalizer.bangkok_abbreviations),
            'total_patterns': {
                'remove': len(self.bangkok_normalizer.bangkok_patterns['remove_patterns']),
                'cleanup': len(self.bangkok_normalizer.bangkok_patterns['cleanup_patterns'])
            }
        }
    
    def enable_step(self, step_name: str, enabled: bool = True):
        """Enable or disable a normalization step."""
        for step in self.normalization_pipeline:
            if step['name'] == step_name:
                step['enabled'] = enabled
                logger.info(f"Step '{step_name}' {'enabled' if enabled else 'disabled'}")
                return
        
        logger.warning(f"Step '{step_name}' not found in pipeline")
    
    def get_step_info(self, step_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific pipeline step."""
        for step in self.normalization_pipeline:
            if step['name'] == step_name:
                return step.copy()
        return None
    
    def add_custom_step(self, name: str, description: str, normalizer: BaseNormalizer, enabled: bool = True):
        """Add a custom normalization step to the pipeline."""
        custom_step = {
            'name': name,
            'description': description,
            'normalizer': normalizer,
            'enabled': enabled
        }
        
        self.normalization_pipeline.append(custom_step)
        logger.info(f"Added custom step '{name}' to normalization pipeline")
    
    def validate_normalization(self, original: Dict[str, Any], normalized: Dict[str, Any]) -> Dict[str, Any]:
        """Validate normalization results."""
        validation = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'quality_score': 0.0
        }
        
        # Check required fields
        required_fields = ['name', 'description', 'area']
        for field in required_fields:
            if field not in normalized or not normalized[field]:
                validation['warnings'].append(f"Missing or empty {field}")
                validation['quality_score'] -= 0.1
        
        # Check field lengths
        if 'name' in normalized and normalized['name']:
            if len(normalized['name']) > self.base_normalizer.max_title_length:
                validation['warnings'].append(f"Name too long: {len(normalized['name'])} chars")
                validation['quality_score'] -= 0.05
        
        if 'description' in normalized and normalized['description']:
            if len(normalized['description']) > self.base_normalizer.max_description_length:
                validation['warnings'].append(f"Description too long: {len(normalized['description'])} chars")
                validation['quality_score'] -= 0.05
        
        if 'area' in normalized and normalized['area']:
            if len(normalized['area']) > self.base_normalizer.max_area_length:
                validation['warnings'].append(f"Area too long: {len(normalized['area'])} chars")
                validation['quality_score'] -= 0.05
        
        # Check for HTML tags
        for field in ['name', 'description', 'area']:
            if field in normalized and normalized[field]:
                if '<' in str(normalized[field]) or '>' in str(normalized[field]):
                    validation['errors'].append(f"HTML tags found in {field}")
                    validation['quality_score'] -= 0.2
        
        # Check for excessive special characters
        for field in ['name', 'description']:
            if field in normalized and normalized[field]:
                special_char_count = sum(1 for c in str(normalized[field]) if not c.isalnum() and c != ' ')
                if special_char_count > len(str(normalized[field])) * 0.3:  # More than 30% special chars
                    validation['warnings'].append(f"Excessive special characters in {field}")
                    validation['quality_score'] -= 0.1
        
        # Calculate final quality score
        validation['quality_score'] = max(0.0, min(1.0, validation['quality_score'] + 1.0))
        
        # Mark as invalid if there are errors
        if validation['errors']:
            validation['is_valid'] = False
        
        return validation
    
    def reset_stats(self):
        """Reset normalization statistics."""
        self.normalization_stats = {
            'total_places_processed': 0,
            'total_fields_normalized': 0,
            'total_characters_removed': 0,
            'bangkok_areas_standardized': 0,
            'quality_improvements': []
        }
        logger.info("Normalization statistics reset")


# Фабрика для создания универсального нормализатора
def create_universal_normalizer(enable_bangkok_normalization: bool = True) -> UniversalNormalizer:
    """Create and return a universal normalizer instance."""
    return UniversalNormalizer(enable_bangkok_normalization)
