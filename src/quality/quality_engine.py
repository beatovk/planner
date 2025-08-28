#!/usr/bin/env python3
"""
Quality Engine for Bangkok Places Parser.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """Quality levels for places."""
    EXCELLENT = "excellent"  # 0.9-1.0
    GOOD = "good"           # 0.8-0.89
    ACCEPTABLE = "acceptable"  # 0.7-0.79
    POOR = "poor"           # 0.6-0.69
    UNACCEPTABLE = "unacceptable"  # <0.6


@dataclass
class QualityMetrics:
    """Quality metrics for a place."""
    completeness: float = 0.0
    photo_score: float = 0.0
    data_freshness: float = 0.0
    source_reliability: float = 0.0
    validation_score: float = 0.0
    
    def get_overall_score(self) -> float:
        """Calculate overall quality score."""
        weights = {
            'completeness': 0.4,
            'photo_score': 0.3,
            'data_freshness': 0.15,
            'source_reliability': 0.1,
            'validation_score': 0.05
        }
        
        overall = (
            self.completeness * weights['completeness'] +
            self.photo_score * weights['photo_score'] +
            self.data_freshness * weights['data_freshness'] +
            self.source_reliability * weights['source_reliability'] +
            self.validation_score * weights['validation_score']
        )
        
        return round(overall, 3)
    
    def get_quality_level(self) -> QualityLevel:
        """Get quality level based on overall score."""
        score = self.get_overall_score()
        
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.8:
            return QualityLevel.GOOD
        elif score >= 0.7:
            return QualityLevel.ACCEPTABLE
        elif score >= 0.6:
            return QualityLevel.POOR
        else:
            return QualityLevel.UNACCEPTABLE


class QualityEngine:
    """Engine for assessing place quality."""
    
    def __init__(self, min_completeness: float = 0.7, require_photo: bool = True):
        """Initialize quality engine."""
        self.min_completeness = min_completeness
        self.require_photo = require_photo
        
        # Required fields for completeness calculation
        self.required_fields = [
            'name', 'city', 'domain', 'url'
        ]
        
        # Important fields (weighted higher)
        self.important_fields = [
            'description', 'address', 'geo_lat', 'geo_lng', 'tags', 'flags'
        ]
        
        # Optional fields (weighted lower)
        self.optional_fields = [
            'phone', 'email', 'website', 'hours', 'price_level', 'rating'
        ]
        
        # Field weights for completeness calculation
        self.field_weights = {
            'name': 0.15,
            'city': 0.10,
            'domain': 0.05,
            'url': 0.10,
            'description': 0.20,
            'address': 0.15,
            'geo_lat': 0.05,
            'geo_lng': 0.05,
            'tags': 0.10,
            'flags': 0.05
        }
        
        # Source reliability scores
        self.source_reliability = {
            'timeout.com': 0.9,
            'bk-magazine.com': 0.85,
            'bangkokpost.com': 0.8,
            'coconuts.co': 0.75,
            'thesmartlocal.com': 0.8,
            'tripadvisor.com': 0.85,
            'google.com': 0.9,
            'facebook.com': 0.7,
            'instagram.com': 0.6
        }
        
        # Statistics
        self.stats = {
            'total_assessed': 0,
            'accepted': 0,
            'rejected': 0,
            'avg_completeness': 0.0,
            'avg_photo_score': 0.0,
            'avg_overall_score': 0.0
        }
    
    def assess_place_quality(self, place_data: Dict[str, Any]) -> Tuple[bool, QualityMetrics, Dict[str, Any]]:
        """Assess quality of a place.
        
        Returns:
            Tuple[bool, QualityMetrics, Dict[str, Any]]: (is_acceptable, metrics, details)
        """
        try:
            # Calculate completeness
            completeness = self._calculate_completeness(place_data)
            
            # Calculate photo score
            photo_score = self._calculate_photo_score(place_data)
            
            # Calculate data freshness
            data_freshness = self._calculate_data_freshness(place_data)
            
            # Calculate source reliability
            source_reliability = self._calculate_source_reliability(place_data)
            
            # Calculate validation score
            validation_score = self._calculate_validation_score(place_data)
            
            # Create quality metrics
            metrics = QualityMetrics(
                completeness=completeness,
                photo_score=photo_score,
                data_freshness=data_freshness,
                source_reliability=source_reliability,
                validation_score=validation_score
            )
            
            # Determine if place is acceptable
            is_acceptable = self._is_place_acceptable(metrics)
            
            # Generate quality details
            details = self._generate_quality_details(place_data, metrics)
            
            # Update statistics
            self._update_statistics(metrics, is_acceptable)
            
            return is_acceptable, metrics, details
            
        except Exception as e:
            logger.error(f"Error assessing place quality: {e}")
            # Return default values on error
            default_metrics = QualityMetrics()
            default_details = {'error': str(e)}
            return False, default_metrics, default_details
    
    def _calculate_completeness(self, place_data: Dict[str, Any]) -> float:
        """Calculate completeness score for a place."""
        total_score = 0.0
        max_score = 0.0
        
        # Check required fields
        for field in self.required_fields:
            weight = self.field_weights.get(field, 0.1)
            max_score += weight
            
            if self._is_field_present(place_data, field):
                total_score += weight
        
        # Check important fields
        for field in self.important_fields:
            weight = self.field_weights.get(field, 0.1)
            max_score += weight
            
            if self._is_field_present(place_data, field):
                total_score += weight
        
        # Check optional fields (bonus points)
        for field in self.optional_fields:
            if self._is_field_present(place_data, field):
                total_score += 0.02  # Small bonus for optional fields
        
        # Normalize to 0-1 range
        if max_score > 0:
            completeness = min(total_score / max_score, 1.0)
        else:
            completeness = 0.0
        
        return round(completeness, 3)
    
    def _calculate_photo_score(self, place_data: Dict[str, Any]) -> float:
        """Calculate photo quality score."""
        photos = place_data.get('photos', [])
        image_url = place_data.get('image_url')
        
        if not photos and not image_url:
            return 0.0
        
        # Check if we have any photos
        has_photos = len(photos) > 0 or bool(image_url)
        
        if not has_photos:
            return 0.0
        
        # Basic photo score
        score = 0.5
        
        # Bonus for multiple photos
        if len(photos) > 1:
            score += 0.2
        
        # Bonus for high-quality photo indicators
        if image_url:
            if any(ext in image_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                score += 0.1
            
            # Check for high-resolution indicators
            if any(indicator in image_url.lower() for indicator in ['large', 'high', 'hd', 'original']):
                score += 0.1
        
        # Bonus for photo metadata
        if photos:
            for photo in photos:
                if isinstance(photo, dict):
                    # Check for photo metadata
                    if photo.get('width') and photo.get('height'):
                        score += 0.05
                    if photo.get('alt_text'):
                        score += 0.05
        
        return min(score, 1.0)
    
    def _calculate_data_freshness(self, place_data: Dict[str, Any]) -> float:
        """Calculate data freshness score."""
        # Check for last_updated field
        last_updated = place_data.get('last_updated')
        if not last_updated:
            return 0.5  # Default score for unknown freshness
        
        try:
            # Parse date (assuming ISO format or similar)
            if isinstance(last_updated, str):
                # Simple date parsing (can be enhanced)
                if '2024' in last_updated or '2025' in last_updated:
                    return 0.9
                elif '2023' in last_updated:
                    return 0.7
                elif '2022' in last_updated:
                    return 0.5
                else:
                    return 0.3
            else:
                return 0.5
        except:
            return 0.5
    
    def _calculate_source_reliability(self, place_data: Dict[str, Any]) -> float:
        """Calculate source reliability score."""
        domain = place_data.get('domain', '')
        if not domain:
            return 0.5
        
        # Clean domain
        domain = domain.lower().replace('www.', '')
        
        # Get reliability score
        reliability = self.source_reliability.get(domain, 0.5)
        
        # Bonus for HTTPS
        url = place_data.get('url', '')
        if url and url.startswith('https://'):
            reliability += 0.05
        
        return min(reliability, 1.0)
    
    def _calculate_validation_score(self, place_data: Dict[str, Any]) -> float:
        """Calculate validation score."""
        score = 0.0
        
        # Check name validation
        name = place_data.get('name', '')
        if name and len(name.strip()) > 0:
            score += 0.2
            if len(name) > 5:  # Reasonable name length
                score += 0.1
        
        # Check URL validation
        url = place_data.get('url', '')
        if url and self._is_valid_url(url):
            score += 0.2
        
        # Check coordinate validation
        lat = place_data.get('geo_lat')
        lng = place_data.get('geo_lng')
        if lat is not None and lng is not None:
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                score += 0.2
        
        # Check address validation
        address = place_data.get('address', '')
        if address and len(address.strip()) > 10:  # Reasonable address length
            score += 0.1
        
        # Check tags validation
        tags = place_data.get('tags', [])
        if tags and isinstance(tags, list) and len(tags) > 0:
            score += 0.1
        
        # Check description validation
        description = place_data.get('description', '')
        if description and len(description.strip()) > 20:  # Reasonable description length
            score += 0.1
        
        return min(score, 1.0)
    
    def _is_field_present(self, place_data: Dict[str, Any], field: str) -> bool:
        """Check if a field is present and has meaningful content."""
        value = place_data.get(field)
        
        if value is None:
            return False
        
        if isinstance(value, str):
            return len(value.strip()) > 0
        
        if isinstance(value, list):
            return len(value) > 0
        
        if isinstance(value, (int, float)):
            return True
        
        return bool(value)
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        if not url:
            return False
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))
    
    def _is_place_acceptable(self, metrics: QualityMetrics) -> bool:
        """Determine if a place meets quality requirements."""
        # Check completeness requirement
        if metrics.completeness < self.min_completeness:
            return False
        
        # Check photo requirement if enabled
        if self.require_photo and metrics.photo_score == 0.0:
            return False
        
        # Check overall quality threshold
        overall_score = metrics.get_overall_score()
        if overall_score < 0.6:  # Minimum acceptable overall score
            return False
        
        return True
    
    def _generate_quality_details(self, place_data: Dict[str, Any], metrics: QualityMetrics) -> Dict[str, Any]:
        """Generate detailed quality information."""
        details = {
            'overall_score': metrics.get_overall_score(),
            'quality_level': metrics.get_quality_level().value,
            'field_analysis': {},
            'recommendations': [],
            'warnings': []
        }
        
        # Analyze individual fields
        for field in self.required_fields + self.important_fields + self.optional_fields:
            is_present = self._is_field_present(place_data, field)
            details['field_analysis'][field] = {
                'present': is_present,
                'value': place_data.get(field),
                'required': field in self.required_fields,
                'important': field in self.important_fields
            }
        
        # Generate recommendations
        if metrics.completeness < 0.8:
            details['recommendations'].append("Improve data completeness")
        
        if metrics.photo_score == 0.0:
            details['recommendations'].append("Add photos")
        elif metrics.photo_score < 0.5:
            details['recommendations'].append("Improve photo quality")
        
        if metrics.data_freshness < 0.7:
            details['recommendations'].append("Update data freshness")
        
        # Generate warnings
        if metrics.completeness < self.min_completeness:
            details['warnings'].append(f"Completeness below threshold ({metrics.completeness} < {self.min_completeness})")
        
        if self.require_photo and metrics.photo_score == 0.0:
            details['warnings'].append("Photo required but not provided")
        
        if metrics.get_overall_score() < 0.6:
            details['warnings'].append("Overall quality below acceptable threshold")
        
        return details
    
    def _update_statistics(self, metrics: QualityMetrics, is_acceptable: bool):
        """Update quality statistics."""
        self.stats['total_assessed'] += 1
        
        if is_acceptable:
            self.stats['accepted'] += 1
        else:
            self.stats['rejected'] += 1
        
        # Update averages
        total = self.stats['total_assessed']
        current_avg_completeness = self.stats['avg_completeness']
        current_avg_photo_score = self.stats['avg_photo_score']
        current_avg_overall_score = self.stats['avg_overall_score']
        
        # Calculate new averages
        self.stats['avg_completeness'] = round(
            (current_avg_completeness * (total - 1) + metrics.completeness) / total, 3
        )
        self.stats['avg_photo_score'] = round(
            (current_avg_photo_score * (total - 1) + metrics.photo_score) / total, 3
        )
        self.stats['avg_overall_score'] = round(
            (current_avg_overall_score * (total - 1) + metrics.get_overall_score()) / total, 3
        )
    
    def get_quality_statistics(self) -> Dict[str, Any]:
        """Get comprehensive quality statistics."""
        stats = self.stats.copy()
        
        # Calculate additional metrics
        if stats['total_assessed'] > 0:
            stats['acceptance_rate'] = round(stats['accepted'] / stats['total_assessed'], 3)
            stats['rejection_rate'] = round(stats['rejected'] / stats['total_assessed'], 3)
        else:
            stats['acceptance_rate'] = 0.0
            stats['rejection_rate'] = 0.0
        
        return stats
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """Get quality summary for reporting."""
        stats = self.get_quality_statistics()
        
        summary = {
            'total_assessed': stats['total_assessed'],
            'acceptance_rate': f"{stats['acceptance_rate']:.1%}",
            'rejection_rate': f"{stats['rejection_rate']:.1%}",
            'average_scores': {
                'completeness': f"{stats['avg_completeness']:.3f}",
                'photo_score': f"{stats['avg_photo_score']:.3f}",
                'overall': f"{stats['avg_overall_score']:.3f}"
            },
            'quality_distribution': {
                'excellent': 0,
                'good': 0,
                'acceptable': 0,
                'poor': 0,
                'unacceptable': 0
            }
        }
        
        return summary
    
    def reset_statistics(self):
        """Reset quality statistics."""
        for key in self.stats:
            self.stats[key] = 0.0 if 'avg' in key else 0
    
    def export_quality_report(self, output_file: str, places_data: List[Dict[str, Any]]):
        """Export comprehensive quality report."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("Quality Assessment Report\n")
                f.write("=" * 50 + "\n\n")
                
                # Summary
                summary = self.get_quality_summary()
                f.write("Summary:\n")
                f.write("-" * 20 + "\n")
                f.write(f"Total assessed: {summary['total_assessed']}\n")
                f.write(f"Acceptance rate: {summary['acceptance_rate']}\n")
                f.write(f"Rejection rate: {summary['rejection_rate']}\n")
                f.write(f"Average completeness: {summary['average_scores']['completeness']}\n")
                f.write(f"Average photo score: {summary['average_scores']['photo_score']}\n")
                f.write(f"Average overall score: {summary['average_scores']['overall']}\n\n")
                
                # Detailed analysis
                f.write("Detailed Analysis:\n")
                f.write("-" * 20 + "\n")
                
                for i, place_data in enumerate(places_data, 1):
                    is_acceptable, metrics, details = self.assess_place_quality(place_data)
                    
                    f.write(f"Place {i}: {place_data.get('name', 'Unknown')}\n")
                    f.write(f"  Overall score: {details['overall_score']}\n")
                    f.write(f"  Quality level: {details['quality_level']}\n")
                    f.write(f"  Completeness: {metrics.completeness}\n")
                    f.write(f"  Photo score: {metrics.photo_score}\n")
                    f.write(f"  Acceptable: {'Yes' if is_acceptable else 'No'}\n")
                    
                    if details['warnings']:
                        f.write(f"  Warnings: {', '.join(details['warnings'])}\n")
                    
                    if details['recommendations']:
                        f.write(f"  Recommendations: {', '.join(details['recommendations'])}\n")
                    
                    f.write("\n")
                
            logger.info(f"Quality report exported to {output_file}")
            
        except Exception as e:
            logger.error(f"Error exporting quality report: {e}")


# Фабрика для создания движка качества
def create_quality_engine(min_completeness: float = 0.7, require_photo: bool = True) -> QualityEngine:
    """Create and return a quality engine instance."""
    return QualityEngine(min_completeness, require_photo)
