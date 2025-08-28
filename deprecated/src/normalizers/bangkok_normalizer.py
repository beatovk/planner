#!/usr/bin/env python3
"""
Bangkok-specific normalizer with area synonyms and local knowledge.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from .base_normalizer import BaseNormalizer
import re

logger = logging.getLogger(__name__)


class BangkokNormalizer(BaseNormalizer):
    """Bangkok-specific normalizer with area synonyms and local knowledge."""
    
    def __init__(self):
        """Initialize Bangkok normalizer."""
        super().__init__()
        
        # Bangkok area synonyms and standardizations
        self.area_synonyms = {
            # Sukhumvit area variations
            'sukhumvit': ['sukhumvit', 'sukhumvit road', 'sukhumvit soi', 'sukhumvit area'],
            'sukhumvit soi 11': ['soi 11', 'sukhumvit 11', 'sukhumvit soi 11', 'soi 11 sukhumvit'],
            'sukhumvit soi 23': ['soi 23', 'sukhumvit 23', 'sukhumvit soi 23', 'soi 23 sukhumvit'],
            'sukhumvit soi 33': ['soi 33', 'sukhumvit 33', 'sukhumvit soi 33', 'soi 33 sukhumvit'],
            'sukhumvit soi 55': ['soi 55', 'sukhumvit 55', 'sukhumvit soi 55', 'soi 55 sukhumvit', 'thonglor'],
            'sukhumvit soi 63': ['soi 63', 'sukhumvit 63', 'sukhumvit soi 63', 'soi 63 sukhumvit', 'ekkamai'],
            
            # Silom area variations
            'silom': ['silom', 'silom road', 'silom area', 'silom district'],
            'silom soi 4': ['soi 4', 'silom 4', 'silom soi 4', 'soi 4 silom'],
            'silom soi 6': ['soi 6', 'silom 6', 'silom soi 6', 'soi 6 silom'],
            
            # Sathorn area variations
            'sathorn': ['sathorn', 'sathorn road', 'sathorn area', 'sathorn district', 'sathorn soi'],
            'sathorn soi 1': ['soi 1', 'sathorn 1', 'sathorn soi 1', 'soi 1 sathorn'],
            'sathorn soi 12': ['soi 12', 'sathorn 12', 'sathorn soi 12', 'soi 12 sathorn'],
            
            # Siam area variations
            'siam': ['siam', 'siam area', 'siam district', 'siam square', 'siam center'],
            'siam square': ['siam square', 'siam sq', 'siam square area'],
            'siam paragon': ['siam paragon', 'paragon', 'siam paragon mall'],
            
            # Pratunam area variations
            'pratunam': ['pratunam', 'pratunam area', 'pratunam district', 'pratunam market'],
            'pratunam market': ['pratunam market', 'pratunam', 'pratunam area'],
            
            # Chinatown area variations
            'chinatown': ['chinatown', 'yaowarat', 'yaowarat road', 'chinatown area', 'yaowarat area'],
            'yaowarat': ['yaowarat', 'yaowarat road', 'chinatown', 'chinatown area'],
            
            # Khao San area variations
            'khao san': ['khao san', 'khao san road', 'khao san area', 'khao san district'],
            'khao san road': ['khao san road', 'khao san', 'khao san area'],
            
            # Chatuchak area variations
            'chatuchak': ['chatuchak', 'chatuchak weekend market', 'chatuchak market', 'chatuchak area'],
            'chatuchak weekend market': ['chatuchak weekend market', 'chatuchak', 'chatuchak market'],
            
            # Ari area variations
            'ari': ['ari', 'ari area', 'ari district', 'ari soi'],
            'ari soi 1': ['soi 1', 'ari 1', 'ari soi 1', 'soi 1 ari'],
            'ari soi 4': ['soi 4', 'ari 4', 'ari soi 4', 'soi 4 ari'],
            
            # Lad Phrao area variations
            'lad phrao': ['lad phrao', 'ladphrao', 'lad phrao road', 'lad phrao area'],
            'lad phrao soi 1': ['soi 1', 'lad phrao 1', 'lad phrao soi 1', 'soi 1 lad phrao'],
            
            # Ratchada area variations
            'ratchada': ['ratchada', 'ratchadaphisek', 'ratchadaphisek road', 'ratchada area'],
            'ratchadaphisek': ['ratchadaphisek', 'ratchadaphisek road', 'ratchada', 'ratchada area'],
            
            # Thonglor area variations
            'thonglor': ['thonglor', 'thong lo', 'thong lo soi 55', 'sukhumvit soi 55', 'soi 55'],
            'thong lo': ['thong lo', 'thonglor', 'thong lo soi 55', 'sukhumvit soi 55'],
            
            # Ekkamai area variations
            'ekkamai': ['ekkamai', 'ekkamai soi 63', 'sukhumvit soi 63', 'soi 63'],
            
            # Phrom Phong area variations
            'phrom phong': ['phrom phong', 'phrom phong soi 39', 'sukhumvit soi 39', 'soi 39'],
            'phrom phong soi 39': ['soi 39', 'phrom phong 39', 'phrom phong soi 39', 'sukhumvit soi 39'],
            
            # Asoke area variations
            'asoke': ['asoke', 'asoke soi 21', 'sukhumvit soi 21', 'soi 21'],
            'asoke soi 21': ['soi 21', 'asoke 21', 'asoke soi 21', 'sukhumvit soi 21'],
            
            # Nana area variations
            'nana': ['nana', 'nana soi 4', 'sukhumvit soi 4', 'soi 4'],
            'nana soi 4': ['soi 4', 'nana 4', 'nana soi 4', 'sukhumvit soi 4'],
            
            # Ploenchit area variations
            'ploenchit': ['ploenchit', 'ploenchit road', 'ploenchit area', 'ploenchit district'],
            
            # Wireless area variations
            'wireless': ['wireless', 'wireless road', 'wireless area', 'wireless district'],
            
            # Lumpini area variations
            'lumpini': ['lumpini', 'lumpini park', 'lumpini area', 'lumpini district'],
            'lumpini park': ['lumpini park', 'lumpini', 'lumpini area'],
            
            # Lumphini area variations (alternative spelling)
            'lumphini': ['lumphini', 'lumphini park', 'lumphini area', 'lumphini district'],
            'lumphini park': ['lumphini park', 'lumphini', 'lumphini area'],
            
            # Victory Monument area variations
            'victory monument': ['victory monument', 'victory monument area', 'victory monument district'],
            
            # Mo Chit area variations
            'mo chit': ['mo chit', 'mo chit area', 'mo chit district', 'mo chit bts'],
            'mo chit bts': ['mo chit bts', 'mo chit', 'mo chit area'],
            
            # On Nut area variations
            'on nut': ['on nut', 'on nut soi 77', 'sukhumvit soi 77', 'soi 77'],
            'on nut soi 77': ['soi 77', 'on nut 77', 'on nut soi 77', 'sukhumvit soi 77'],
            
            # Bang Na area variations
            'bang na': ['bang na', 'bang na area', 'bang na district', 'bang na soi'],
            
            # Samut Prakan area variations
            'samut prakan': ['samut prakan', 'samut prakan area', 'samut prakan district', 'samut prakan province'],
            
            # Nonthaburi area variations
            'nonthaburi': ['nonthaburi', 'nonthaburi area', 'nonthaburi district', 'nonthaburi province'],
            
            # Pathum Thani area variations
            'pathum thani': ['pathum thani', 'pathum thani area', 'pathum thani district', 'pathum thani province'],
            
            # Samut Sakhon area variations
            'samut sakhon': ['samut sakhon', 'samut sakhon area', 'samut sakhon district', 'samut sakhon province'],
            
            # Nakhon Pathom area variations
            'nakhon pathom': ['nakhon pathom', 'nakhon pathom area', 'nakhon pathom district', 'nakhon pathom province']
        }
        
        # Bangkok-specific abbreviations
        self.bangkok_abbreviations = {
            'bkk': 'Bangkok',
            'bkk.': 'Bangkok',
            'bk': 'Bangkok',
            'bk.': 'Bangkok',
            'th': 'Thailand',
            'th.': 'Thailand',
            'soi': 'Soi',
            'soi.': 'Soi',
            'rd': 'Road',
            'rd.': 'Road',
            'st': 'Street',
            'st.': 'Street',
            'ave': 'Avenue',
            'ave.': 'Avenue',
            'blvd': 'Boulevard',
            'blvd.': 'Boulevard',
            'pkwy': 'Parkway',
            'pkwy.': 'Parkway',
            'sq': 'Square',
            'sq.': 'Square',
            'pl': 'Place',
            'pl.': 'Place',
            'ct': 'Court',
            'ct.': 'Court',
            'ln': 'Lane',
            'ln.': 'Lane',
            'dr': 'Drive',
            'dr.': 'Drive'
        }
        
        # Merge with base abbreviations
        self.abbreviations.update(self.bangkok_abbreviations)
        
        # Bangkok-specific text cleaning patterns
        self.bangkok_patterns = {
            'remove_patterns': [
                r'\b(restaurant|cafe|bar|club|pub|lounge|bistro|eatery)\s+(in|at|near|close to)\b',
                r'\b(located|situated|found|situated)\s+(in|at|near|close to)\b',
                r'\b(just|only|mere|short)\s+(minutes?|mins?|walk|distance)\b',
                r'\b(conveniently|easily|quickly)\s+(accessible|reachable|reach)\b'
            ],
            'cleanup_patterns': [
                (r'\b(amazing|incredible|fantastic|wonderful|excellent|great|good|nice)\s+', ''),
                (r'\b(best|top|favorite|popular|trendy|hip|cool|awesome)\s+', ''),
                (r'\b(must-visit|must-try|essential|definitive|ultimate|complete)\s+', ''),
                (r'\b(authentic|traditional|local|thai|asian|international)\s+', ''),
                (r'\b(restaurant|cafe|bar|club|pub|lounge|bistro|eatery)\s*$', ''),
                (r'\b(in|at|near|close to|within|around)\s+(bangkok|bkk|thailand)\b', ''),
                (r'\b(bangkok|bkk|thailand)\s+(restaurant|cafe|bar|club|pub|lounge|bistro|eatery)\b', '')
            ]
        }
    
    def normalize_area(self, area: str) -> str:
        """Normalize area field with Bangkok-specific knowledge."""
        if not area:
            return area
        
        # First apply base normalization
        normalized = super().normalize_area(area)
        
        # Apply Bangkok-specific area standardization
        normalized = self._standardize_bangkok_area(normalized)
        
        # Clean up common Bangkok patterns
        normalized = self._cleanup_bangkok_patterns(normalized)
        
        return normalized
    
    def normalize_description(self, description: str) -> str:
        """Normalize description with Bangkok-specific cleaning."""
        if not description:
            return description
        
        # First apply base normalization
        normalized = super().normalize_description(description)
        
        # Apply Bangkok-specific cleaning
        normalized = self._cleanup_bangkok_description(normalized)
        
        return normalized
    
    def normalize_specific_field(self, field_name: str, value: Any) -> Any:
        """Normalize a specific field with Bangkok knowledge."""
        if field_name == 'area':
            return self.normalize_area(str(value) if value else '')
        elif field_name == 'description':
            return self.normalize_description(str(value) if value else '')
        elif field_name == 'name':
            return self.normalize_title(str(value) if value else '')
        else:
            return value
    
    def _standardize_bangkok_area(self, area: str) -> str:
        """Standardize Bangkok area names using synonyms."""
        if not area:
            return area
        
        area_lower = area.lower().strip()
        
        # Find matching standard area name
        for standard_name, synonyms in self.area_synonyms.items():
            if area_lower in synonyms:
                return standard_name.title()
        
        # If no exact match, try partial matching
        for standard_name, synonyms in self.area_synonyms.items():
            for synonym in synonyms:
                if synonym in area_lower or area_lower in synonym:
                    return standard_name.title()
        
        # If still no match, return the original (normalized)
        return area
    
    def _cleanup_bangkok_patterns(self, text: str) -> str:
        """Clean up common Bangkok-specific patterns."""
        if not text:
            return text
        
        # Remove unwanted patterns
        for pattern in self.bangkok_patterns['remove_patterns']:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Clean up specific patterns
        for pattern, replacement in self.bangkok_patterns['cleanup_patterns']:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _cleanup_bangkok_description(self, description: str) -> str:
        """Clean up Bangkok-specific description patterns."""
        if not description:
            return description
        
        # Remove common marketing phrases
        marketing_phrases = [
            r'\b(amazing|incredible|fantastic|wonderful|excellent|great|good|nice)\s+(place|spot|venue|location)\b',
            r'\b(best|top|favorite|popular|trendy|hip|cool|awesome)\s+(place|spot|venue|location)\b',
            r'\b(must-visit|must-try|essential|definitive|ultimate|complete)\s+(place|spot|venue|location)\b',
            r'\b(authentic|traditional|local|thai|asian|international)\s+(cuisine|food|experience|atmosphere)\b',
            r'\b(conveniently|easily|quickly)\s+(located|situated|accessible|reachable)\b',
            r'\b(just|only|mere|short)\s+(minutes?|mins?|walk|distance)\s+(from|to|away)\b'
        ]
        
        for pattern in marketing_phrases:
            description = re.sub(pattern, '', description, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        description = re.sub(r'\s+', ' ', description)
        
        return description.strip()
    
    def get_bangkok_area_synonyms(self, area: str) -> List[str]:
        """Get all synonyms for a given Bangkok area."""
        area_lower = area.lower().strip()
        
        for standard_name, synonyms in self.area_synonyms.items():
            if area_lower == standard_name.lower():
                return synonyms
        
        return []
    
    def get_standard_area_name(self, area: str) -> Optional[str]:
        """Get the standard area name for a given area."""
        area_lower = area.lower().strip()
        
        for standard_name, synonyms in self.area_synonyms.items():
            if area_lower in synonyms:
                return standard_name.title()
        
        return None
    
    def is_bangkok_area(self, area: str) -> bool:
        """Check if an area is a known Bangkok area."""
        area_lower = area.lower().strip()
        
        for standard_name, synonyms in self.area_synonyms.items():
            if area_lower in synonyms:
                return True
        
        return False
    
    def get_bangkok_area_stats(self) -> Dict[str, Any]:
        """Get statistics about Bangkok areas."""
        total_areas = len(self.area_synonyms)
        total_synonyms = sum(len(synonyms) for synonyms in self.area_synonyms.values())
        
        # Group by area type
        area_types = {
            'sukhumvit': [area for area in self.area_synonyms.keys() if 'sukhumvit' in area.lower()],
            'silom': [area for area in self.area_synonyms.keys() if 'silom' in area.lower()],
            'sathorn': [area for area in self.area_synonyms.keys() if 'sathorn' in area.lower()],
            'siam': [area for area in self.area_synonyms.keys() if 'siam' in area.lower()],
            'chinatown': [area for area in self.area_synonyms.keys() if 'chinatown' in area.lower() or 'yaowarat' in area.lower()],
            'other': [area for area in self.area_synonyms.keys() if not any(keyword in area.lower() for keyword in ['sukhumvit', 'silom', 'sathorn', 'siam', 'chinatown', 'yaowarat'])]
        }
        
        return {
            'total_areas': total_areas,
            'total_synonyms': total_synonyms,
            'average_synonyms_per_area': round(total_synonyms / total_areas, 2),
            'area_types': {k: len(v) for k, v in area_types.items()},
            'area_details': area_types
        }
