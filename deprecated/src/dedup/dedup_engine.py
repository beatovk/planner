#!/usr/bin/env python3
"""
Deduplication Engine for Bangkok Places Parser.
"""

import logging
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)


@dataclass
class DedupCandidate:
    """Candidate for deduplication analysis."""
    place_id: str
    name: str
    city: str
    domain: str
    geo_lat: Optional[float]
    geo_lng: Optional[float]
    address: Optional[str]
    url: Optional[str]
    raw_data: Dict[str, Any]
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Normalize name for comparison
        self.name_normalized = self._normalize_name(self.name)
        
        # Generate identity key
        self.identity_key = self._generate_identity_key()
        
        # Generate address hash
        self.address_hash = self._generate_address_hash()
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison."""
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = [
            "the ", "a ", "an ", "best ", "top ", "famous ", "popular ",
            "amazing ", "incredible ", "fantastic ", "excellent "
        ]
        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
        
        # Remove common suffixes
        suffixes_to_remove = [
            " restaurant", " cafe", " bar", " club", " shop", " store",
            " market", " mall", " hotel", " resort", " spa", " museum"
        ]
        for suffix in suffixes_to_remove:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
        
        # Clean up extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _generate_identity_key(self) -> str:
        """Generate identity key from core fields."""
        # Core components for identity
        components = [
            self.name_normalized,
            self.city.lower() if self.city else "",
            self.domain.lower() if self.domain else "",
        ]
        
        # Add geo coordinates if available (rounded to 3 decimal places)
        if self.geo_lat is not None and self.geo_lng is not None:
            lat_rounded = round(self.geo_lat, 3)
            lng_rounded = round(self.geo_lng, 3)
            components.extend([str(lat_rounded), str(lng_rounded)])
        
        # Join and hash
        key_string = "|".join(filter(None, components))
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def _generate_address_hash(self) -> str:
        """Generate hash from address for comparison."""
        if not self.address:
            return ""
        
        # Normalize address
        address_normalized = self._normalize_address(self.address)
        
        # Hash the normalized address
        return hashlib.md5(address_normalized.encode('utf-8')).hexdigest()
    
    def _normalize_address(self, address: str) -> str:
        """Normalize address for comparison."""
        if not address:
            return ""
        
        # Convert to lowercase
        normalized = address.lower()
        
        # Remove common words that don't affect uniqueness
        common_words = [
            "bangkok", "thailand", "thai", "street", "road", "soi", "lane",
            "building", "floor", "room", "suite", "tower", "plaza", "center"
        ]
        
        for word in common_words:
            # Remove word with surrounding spaces
            normalized = re.sub(r'\b' + re.escape(word) + r'\b', '', normalized)
        
        # Clean up extra spaces and punctuation
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized


class DedupEngine:
    """Engine for deduplicating places using multiple strategies."""
    
    def __init__(self, fuzzy_threshold: float = 0.86, geo_tolerance: float = 0.001):
        """Initialize deduplication engine."""
        self.fuzzy_threshold = fuzzy_threshold
        self.geo_tolerance = geo_tolerance
        
        # Storage for processed places
        self.processed_places: Dict[str, DedupCandidate] = {}
        self.identity_groups: Dict[str, List[str]] = {}
        self.fuzzy_groups: Dict[str, List[str]] = {}
        self.address_groups: Dict[str, List[str]] = {}
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'duplicates_found': 0,
            'identity_matches': 0,
            'fuzzy_matches': 0,
            'address_matches': 0,
            'geo_matches': 0
        }
    
    def add_place(self, place_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Add a place and check for duplicates.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_duplicate, duplicate_place_id)
        """
        try:
            # Create candidate
            candidate = DedupCandidate(
                place_id=place_data.get('id', str(hash(str(place_data)))),
                name=place_data.get('name', ''),
                city=place_data.get('city', ''),
                domain=place_data.get('domain', ''),
                geo_lat=place_data.get('geo_lat'),
                geo_lng=place_data.get('geo_lng'),
                address=place_data.get('address'),
                url=place_data.get('url'),
                raw_data=place_data
            )
            
            # Check for duplicates
            duplicate_id = self._check_duplicates(candidate)
            
            if duplicate_id:
                # This is a duplicate
                self.stats['duplicates_found'] += 1
                return True, duplicate_id
            else:
                # This is a new place
                self._add_new_place(candidate)
                self.stats['total_processed'] += 1
                return False, None
                
        except Exception as e:
            logger.error(f"Error processing place for deduplication: {e}")
            return False, None
    
    def _check_duplicates(self, candidate: DedupCandidate) -> Optional[str]:
        """Check if candidate is a duplicate of existing places."""
        # Strategy 1: Identity key exact match
        duplicate_id = self._check_identity_match(candidate)
        if duplicate_id:
            self.stats['identity_matches'] += 1
            return duplicate_id
        
        # Strategy 2: Fuzzy name matching
        duplicate_id = self._check_fuzzy_match(candidate)
        if duplicate_id:
            self.stats['fuzzy_matches'] += 1
            return duplicate_id
        
        # Strategy 3: Address matching
        duplicate_id = self._check_address_match(candidate)
        if duplicate_id:
            self.stats['address_matches'] += 1
            return duplicate_id
        
        # Strategy 4: Geographic proximity
        duplicate_id = self._check_geo_match(candidate)
        if duplicate_id:
            self.stats['geo_matches'] += 1
            return duplicate_id
        
        return None
    
    def _check_identity_match(self, candidate: DedupCandidate) -> Optional[str]:
        """Check for exact identity key match."""
        if candidate.identity_key in self.identity_groups:
            # Found exact match
            existing_place_id = self.identity_groups[candidate.identity_key][0]
            logger.debug(f"Identity match: {candidate.place_id} matches {existing_place_id}")
            return existing_place_id
        
        return None
    
    def _check_fuzzy_match(self, candidate: DedupCandidate) -> Optional[str]:
        """Check for fuzzy name matching."""
        if not candidate.name_normalized:
            return None
        
        best_match = None
        best_ratio = 0.0
        
        for existing_id, existing_candidate in self.processed_places.items():
            if not existing_candidate.name_normalized:
                continue
            
            # Calculate similarity ratio
            ratio = self._calculate_name_similarity(
                candidate.name_normalized,
                existing_candidate.name_normalized
            )
            
            if ratio > best_ratio and ratio >= self.fuzzy_threshold:
                best_ratio = ratio
                best_match = existing_id
        
        if best_match:
            logger.debug(f"Fuzzy match: {candidate.place_id} matches {best_match} (ratio: {best_ratio:.3f})")
            return best_match
        
        return None
    
    def _check_address_match(self, candidate: DedupCandidate) -> Optional[str]:
        """Check for address matching."""
        if not candidate.address_hash:
            return None
        
        # Check if address hash matches any existing place
        for existing_id, existing_candidate in self.processed_places.items():
            if existing_candidate.address_hash and existing_candidate.address_hash == candidate.address_hash:
                # Additional check: compare normalized addresses
                if self._addresses_are_similar(candidate.address, existing_candidate.address):
                    logger.debug(f"Address match: {candidate.place_id} matches {existing_id}")
                    return existing_id
        
        return None
    
    def _check_geo_match(self, candidate: DedupCandidate) -> Optional[str]:
        """Check for geographic proximity."""
        if candidate.geo_lat is None or candidate.geo_lng is None:
            return None
        
        best_match = None
        best_distance = float('inf')
        
        for existing_id, existing_candidate in self.processed_places.items():
            if existing_candidate.geo_lat is None or existing_candidate.geo_lng is None:
                continue
            
            # Calculate distance
            distance = self._calculate_geo_distance(
                candidate.geo_lat, candidate.geo_lng,
                existing_candidate.geo_lat, existing_candidate.geo_lng
            )
            
            # Check if within tolerance
            if distance <= self.geo_tolerance and distance < best_distance:
                best_distance = distance
                best_match = existing_id
        
        if best_match:
            logger.debug(f"Geo match: {candidate.place_id} matches {best_match} (distance: {best_distance:.6f})")
            return best_match
        
        return None
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity ratio between two names."""
        if not name1 or not name2:
            return 0.0
        
        # Use SequenceMatcher for similarity
        matcher = SequenceMatcher(None, name1, name2)
        return matcher.ratio()
    
    def _addresses_are_similar(self, addr1: Optional[str], addr2: Optional[str]) -> bool:
        """Check if two addresses are similar."""
        if not addr1 or not addr2:
            return False
        
        # Normalize both addresses
        norm1 = self._normalize_address(addr1)
        norm2 = self._normalize_address(addr2)
        
        if not norm1 or not norm2:
            return False
        
        # Calculate similarity
        similarity = self._calculate_name_similarity(norm1, norm2)
        return similarity >= 0.8  # Higher threshold for addresses
    
    def _normalize_address(self, address: str) -> str:
        """Normalize address for comparison."""
        if not address:
            return ""
        
        # Convert to lowercase
        normalized = address.lower()
        
        # Remove common words that don't affect uniqueness
        common_words = [
            "bangkok", "thailand", "thai", "street", "road", "soi", "lane",
            "building", "floor", "room", "suite", "tower", "plaza", "center"
        ]
        
        for word in common_words:
            # Remove word with surrounding spaces
            normalized = re.sub(r'\b' + re.escape(word) + r'\b', '', normalized)
        
        # Clean up extra spaces and punctuation
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _calculate_geo_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate approximate distance between two coordinates."""
        # Simple Euclidean distance (good enough for small distances)
        # For more accuracy, could use Haversine formula
        lat_diff = lat1 - lat2
        lng_diff = lng1 - lng2
        return (lat_diff ** 2 + lng_diff ** 2) ** 0.5
    
    def _add_new_place(self, candidate: DedupCandidate):
        """Add new place to storage."""
        # Add to processed places
        self.processed_places[candidate.place_id] = candidate
        
        # Add to identity groups
        if candidate.identity_key not in self.identity_groups:
            self.identity_groups[candidate.identity_key] = []
        self.identity_groups[candidate.identity_key].append(candidate.place_id)
        
        # Add to fuzzy groups (by first letter for efficiency)
        if candidate.name_normalized:
            first_letter = candidate.name_normalized[0] if candidate.name_normalized else '?'
            if first_letter not in self.fuzzy_groups:
                self.fuzzy_groups[first_letter] = []
            self.fuzzy_groups[first_letter].append(candidate.place_id)
        
        # Add to address groups
        if candidate.address_hash:
            if candidate.address_hash not in self.address_groups:
                self.address_groups[candidate.address_hash] = []
            self.address_groups[candidate.address_hash].append(candidate.place_id)
    
    def get_duplicate_groups(self) -> List[List[str]]:
        """Get groups of duplicate places."""
        groups = []
        
        # Identity-based groups
        for identity_key, place_ids in self.identity_groups.items():
            if len(place_ids) > 1:
                groups.append(place_ids)
        
        # Fuzzy-based groups
        fuzzy_groups = self._find_fuzzy_groups()
        groups.extend(fuzzy_groups)
        
        # Address-based groups
        address_groups = self._find_address_groups()
        groups.extend(address_groups)
        
        return groups
    
    def _find_fuzzy_groups(self) -> List[List[str]]:
        """Find groups of places with similar names."""
        groups = []
        processed = set()
        
        for place_id, candidate in self.processed_places.items():
            if place_id in processed:
                continue
            
            similar_places = [place_id]
            processed.add(place_id)
            
            for other_id, other_candidate in self.processed_places.items():
                if other_id in processed:
                    continue
                
                if candidate.name_normalized and other_candidate.name_normalized:
                    similarity = self._calculate_name_similarity(
                        candidate.name_normalized,
                        other_candidate.name_normalized
                    )
                    
                    if similarity >= self.fuzzy_threshold:
                        similar_places.append(other_id)
                        processed.add(other_id)
            
            if len(similar_places) > 1:
                groups.append(similar_places)
        
        return groups
    
    def _find_address_groups(self) -> List[List[str]]:
        """Find groups of places with similar addresses."""
        groups = []
        
        for address_hash, place_ids in self.address_groups.items():
            if len(place_ids) > 1:
                groups.append(place_ids)
        
        return groups
    
    def get_dedup_statistics(self) -> Dict[str, Any]:
        """Get deduplication statistics."""
        stats = self.stats.copy()
        
        # Additional calculated stats
        stats['unique_places'] = len(self.processed_places)
        stats['duplicate_groups'] = len(self.get_duplicate_groups())
        stats['total_duplicates'] = sum(len(group) - 1 for group in self.get_duplicate_groups())
        
        # Success rate
        if stats['total_processed'] > 0:
            stats['dedup_rate'] = stats['duplicates_found'] / stats['total_processed']
        else:
            stats['dedup_rate'] = 0.0
        
        return stats
    
    def get_statistics(self) -> Dict[str, Any]:
        """Alias for get_dedup_statistics for compatibility."""
        return self.get_dedup_statistics()
    
    def clear(self):
        """Clear all stored data."""
        self.processed_places.clear()
        self.identity_groups.clear()
        self.fuzzy_groups.clear()
        self.address_groups.clear()
        
        # Reset stats
        for key in self.stats:
            self.stats[key] = 0
    
    def export_duplicates(self, output_file: str):
        """Export duplicate groups to file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("Duplicate Groups Report\n")
                f.write("=" * 50 + "\n\n")
                
                # Identity duplicates
                f.write("Identity-based Duplicates:\n")
                f.write("-" * 30 + "\n")
                for identity_key, place_ids in self.identity_groups.items():
                    if len(place_ids) > 1:
                        f.write(f"Identity Key: {identity_key}\n")
                        for place_id in place_ids:
                            place = self.processed_places[place_id]
                            f.write(f"  - {place_id}: {place.name} ({place.city})\n")
                        f.write("\n")
                
                # Fuzzy duplicates
                f.write("Fuzzy Name Duplicates:\n")
                f.write("-" * 30 + "\n")
                fuzzy_groups = self._find_fuzzy_groups()
                for group in fuzzy_groups:
                    f.write(f"Group: {len(group)} places\n")
                    for place_id in group:
                        place = self.processed_places[place_id]
                        f.write(f"  - {place_id}: {place.name} ({place.city})\n")
                    f.write("\n")
                
                # Address duplicates
                f.write("Address-based Duplicates:\n")
                f.write("-" * 30 + "\n")
                for address_hash, place_ids in self.address_groups.items():
                    if len(place_ids) > 1:
                        f.write(f"Address Hash: {address_hash}\n")
                        for place_id in place_ids:
                            place = self.processed_places[place_id]
                            f.write(f"  - {place_id}: {place.name} - {place.address}\n")
                        f.write("\n")
                
                # Statistics
                stats = self.get_dedup_statistics()
                f.write("Statistics:\n")
                f.write("-" * 30 + "\n")
                for key, value in stats.items():
                    f.write(f"{key}: {value}\n")
                
            logger.info(f"Duplicate report exported to {output_file}")
            
        except Exception as e:
            logger.error(f"Error exporting duplicates: {e}")


# Фабрика для создания движка дедупликации
def create_dedup_engine(fuzzy_threshold: float = 0.86, geo_tolerance: float = 0.001) -> DedupEngine:
    """Create and return a deduplication engine instance."""
    return DedupEngine(fuzzy_threshold, geo_tolerance)
