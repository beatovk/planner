#!/usr/bin/env python3
"""
Pydantic model for Place entity.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import re


class PriceLevel(int, Enum):
    """Price level enumeration."""
    BUDGET = 1      # Street food, local markets
    AFFORDABLE = 2  # Mid-range restaurants, cafes
    MODERATE = 3    # Good restaurants, bars
    EXPENSIVE = 4   # Fine dining, luxury venues
    ULTRA_LUXURY = 5  # Exclusive, VIP venues


class Place(BaseModel):
    """Place entity model."""
    
    # Основные идентификаторы
    id: str = Field(..., description="Unique identifier")
    source: str = Field(..., description="Data source (e.g., 'timeout_bangkok', 'bk_magazine')")
    source_url: str = Field(..., description="Original URL where place was found")
    
    # Основная информация
    name: str = Field(..., description="Place name", min_length=2, max_length=200)
    description: Optional[str] = Field(None, description="Place description", max_length=500)
    
    # Локация
    city: str = Field(default="bangkok", description="City name")
    area: Optional[str] = Field(None, description="District/area name", max_length=100)
    address: Optional[str] = Field(None, description="Full address", max_length=300)
    lat: Optional[float] = Field(None, description="Latitude", ge=-90, le=90)
    lon: Optional[float] = Field(None, description="Longitude", ge=-180, le=180)
    
    # Категоризация
    flags: List[str] = Field(default_factory=list, description="Main category flags")
    tags: List[str] = Field(default_factory=list, description="Additional tags")
    
    # Детали
    price_level: Optional[PriceLevel] = Field(None, description="Price level")
    cuisine: Optional[str] = Field(None, description="Cuisine type", max_length=100)
    atmosphere: Optional[str] = Field(None, description="Atmosphere type", max_length=100)
    
    # Медиа
    image_url: Optional[str] = Field(None, description="Main image URL")
    image_urls: List[str] = Field(default_factory=list, description="Additional image URLs")
    
    # Контакты и информация
    phone: Optional[str] = Field(None, description="Phone number")
    website: Optional[str] = Field(None, description="Website URL")
    hours: Optional[str] = Field(None, description="Opening hours")
    
    # Метрики
    popularity: float = Field(default=0.5, description="Popularity score 0-1")
    quality_score: float = Field(default=0.0, description="Quality score 0-1")
    
    # Технические поля
    extracted_at: datetime = Field(default_factory=datetime.now, description="When data was extracted")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
    version: str = Field(default="1.0", description="Data version")
    
    # Метаданные
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and normalize name."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        
        # Убираем лишние символы
        v = re.sub(r'^\s*[-–—•№]\s*', '', v.strip())
        v = re.sub(r'\s+', ' ', v)
        
        if len(v) < 2:
            raise ValueError("Name too short")
        
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize description."""
        if v is None:
            return v
        
        v = v.strip()
        if len(v) > 500:
            v = v[:497] + "..."
        
        return v
    
    @field_validator('flags')
    @classmethod
    def validate_flags(cls, v: List[str]) -> List[str]:
        """Validate and normalize flags."""
        if not v:
            return []
        
        # Убираем пустые и нормализуем
        normalized = []
        for flag in v:
            if flag and flag.strip():
                normalized.append(flag.strip().lower())
        
        return list(set(normalized))  # Убираем дубликаты
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and normalize tags."""
        if not v:
            return []
        
        # Убираем пустые и нормализуем
        normalized = []
        for tag in v:
            if tag and tag.strip():
                normalized.append(tag.strip().lower())
        
        return list(set(normalized))  # Убираем дубликаты
    
    @field_validator('image_url')
    @classmethod
    def validate_image_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate image URL."""
        if v is None:
            return v
        
        v = v.strip()
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError("Invalid image URL")
        
        return v
    
    @field_validator('website')
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        """Validate website URL."""
        if v is None:
            return v
        
        v = v.strip()
        if v and not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        
        return v
    
    def get_identity_key(self) -> str:
        """Generate identity key for deduplication."""
        # Базовый ключ: название + город + источник
        base_key = f"{self.name.lower()}_{self.city}_{self.source}"
        
        # Добавляем район если есть
        if self.area:
            base_key += f"_{self.area.lower()}"
        
        # Добавляем координаты если есть
        if self.lat and self.lon:
            # Округляем координаты для группировки близких мест
            lat_rounded = round(self.lat, 3)
            lon_rounded = round(self.lon, 3)
            base_key += f"_{lat_rounded}_{lon_rounded}"
        
        return base_key
    
    def get_search_text(self) -> str:
        """Generate search text for FTS5."""
        parts = [self.name]
        
        if self.description:
            parts.append(self.description)
        
        if self.area:
            parts.append(self.area)
        
        if self.cuisine:
            parts.append(self.cuisine)
        
        if self.atmosphere:
            parts.append(self.atmosphere)
        
        if self.tags:
            parts.extend(self.tags)
        
        return " ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'source': self.source,
            'source_url': self.source_url,
            'name': self.name,
            'description': self.description,
            'city': self.city,
            'area': self.area,
            'address': self.address,
            'lat': self.lat,
            'lon': self.lon,
            'flags': ','.join(self.flags) if self.flags else None,
            'tags': ','.join(self.tags) if self.tags else None,
            'price_level': self.price_level.value if self.price_level else None,
            'cuisine': self.cuisine,
            'atmosphere': self.atmosphere,
            'image_url': self.image_url,
            'image_urls': ','.join(self.image_urls) if self.image_urls else None,
            'phone': self.phone,
            'website': self.website,
            'hours': self.hours,
            'popularity': self.popularity,
            'quality_score': self.quality_score,
            'extracted_at': self.extracted_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'version': self.version,
            'metadata': str(self.metadata)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Place':
        """Create Place from dictionary."""
        # Обрабатываем специальные поля
        if 'flags' in data and data['flags']:
            data['flags'] = data['flags'].split(',') if isinstance(data['flags'], str) else data['flags']
        
        if 'tags' in data and data['tags']:
            data['tags'] = data['tags'].split(',') if isinstance(data['tags'], str) else data['tags']
        
        if 'image_urls' in data and data['image_urls']:
            data['image_urls'] = data['image_urls'].split(',') if isinstance(data['image_urls'], str) else data['image_urls']
        
        if 'price_level' in data and data['price_level']:
            data['price_level'] = PriceLevel(data['price_level'])
        
        if 'extracted_at' in data and data['extracted_at']:
            data['extracted_at'] = datetime.fromisoformat(data['extracted_at'])
        
        if 'updated_at' in data and data['updated_at']:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"  # Запрещаем дополнительные поля


class PlaceCreate(BaseModel):
    """Model for creating a new place."""
    source: str
    source_url: str
    name: str
    description: Optional[str] = None
    city: str = "bangkok"
    area: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    flags: List[str] = []
    tags: List[str] = []
    price_level: Optional[PriceLevel] = None
    cuisine: Optional[str] = None
    atmosphere: Optional[str] = None
    image_url: Optional[str] = None
    image_urls: List[str] = []
    phone: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[str] = None
    popularity: float = 0.5
    metadata: Dict[str, Any] = {}


class PlaceUpdate(BaseModel):
    """Model for updating an existing place."""
    name: Optional[str] = None
    description: Optional[str] = None
    area: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    flags: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    price_level: Optional[PriceLevel] = None
    cuisine: Optional[str] = None
    atmosphere: Optional[str] = None
    image_url: Optional[str] = None
    image_urls: Optional[List[str]] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[str] = None
    popularity: Optional[float] = None
    quality_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class PlaceSearch(BaseModel):
    """Model for place search queries."""
    query: Optional[str] = None
    flags: Optional[List[str]] = None
    area: Optional[str] = None
    price_level: Optional[PriceLevel] = None
    cuisine: Optional[str] = None
    limit: int = 20
    offset: int = 0
    sort_by: str = "relevance"  # relevance, quality, popularity, name
    sort_order: str = "desc"     # asc, desc


class PlaceResponse(BaseModel):
    """Model for place API responses."""
    places: List[Place]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool
