#!/usr/bin/env python3
"""
Service for integrating Timeout Bangkok parser with PlacesService.
"""

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
import uuid

from .fetchers.timeout_bangkok_parser import TimeoutBangkokPlacesParser
from .models_places.place import Place
from .db_places import save_places, get_places_by_source
from .cache_places import invalidate_places_cache

logger = logging.getLogger(__name__)

class TimeoutPlacesService:
    """Service for managing Timeout Bangkok places data."""
    
    def __init__(self):
        self.parser = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.parser = TimeoutBangkokPlacesParser()
        await self.parser.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.parser:
            await self.parser.__aexit__(exc_type, exc_val, exc_tb)
    
    async def refresh_places_from_timeout(self, categories: Optional[List[str]] = None) -> Dict:
        """Refresh places data from Timeout Bangkok."""
        logger.info("Starting refresh of places from Timeout Bangkok")
        
        if not self.parser:
            raise RuntimeError("Parser not initialized. Use async context manager.")
        
        start_time = datetime.now()
        stats = {
            'started_at': start_time.isoformat(),
            'categories_processed': 0,
            'articles_processed': 0,
            'places_extracted': 0,
            'places_saved': 0,
            'errors': []
        }
        
        try:
            if categories:
                # Обрабатываем только указанные категории
                logger.info(f"Processing specific categories: {categories}")
                all_places = []
                
                for category in categories:
                    if category in self.parser.categories:
                        for url in self.parser.categories[category]:
                            try:
                                places = await self.parser.scrape_category(category, url)
                                all_places.extend(places)
                                stats['categories_processed'] += 1
                                
                                # Задержка между категориями
                                await asyncio.sleep(2)
                                
                            except Exception as e:
                                error_msg = f"Error processing category {category} from {url}: {e}"
                                logger.error(error_msg)
                                stats['errors'].append(error_msg)
                                continue
                    else:
                        logger.warning(f"Unknown category: {category}")
            else:
                # Обрабатываем все категории
                logger.info("Processing all categories")
                all_places = await self.parser.scrape_all_categories()
                stats['categories_processed'] = len(self.parser.categories)
            
            stats['places_extracted'] = len(all_places)
            logger.info(f"Extracted {len(all_places)} places from Timeout Bangkok")
            
            if all_places:
                # Конвертируем в модели Place
                place_models = self._convert_to_place_models(all_places)
                
                # Сохраняем в базу данных
                saved_count = await save_places(place_models)
                stats['places_saved'] = saved_count
                
                # Инвалидируем кеш
                await invalidate_places_cache()
                
                logger.info(f"Successfully saved {saved_count} places to database")
            else:
                logger.warning("No places extracted from Timeout Bangkok")
        
        except Exception as e:
            error_msg = f"Error during refresh: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
        
        finally:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            stats['completed_at'] = end_time.isoformat()
            stats['duration_seconds'] = duration
            
            logger.info(f"Refresh completed in {duration:.2f} seconds")
            logger.info(f"Stats: {stats}")
        
        return stats
    
    def _convert_to_place_models(self, raw_places: List[Dict]) -> List[Place]:
        """Convert raw place data to Place models."""
        place_models = []
        
        for raw_place in raw_places:
            try:
                # Генерируем уникальный ID
                place_id = f"timeout_{uuid.uuid4().hex[:8]}"
                
                # Создаем Place модель
                place = Place(
                    id=place_id,
                    source=raw_place.get('source', 'timeout_bangkok'),
                    city='bangkok',
                    name=raw_place.get('name', 'Unknown Place'),
                    description=raw_place.get('description', ''),
                    url=raw_place.get('url', ''),
                    image_url=None,  # Пока не извлекаем изображения
                    address=None,     # Пока не извлекаем адреса
                    lat=None,         # Пока не извлекаем координаты
                    lon=None,
                    area=raw_place.get('area'),
                    price_level=raw_place.get('price_level', 2),
                    tags=[],          # Пока пустые теги
                    flags=raw_place.get('flags', []),
                    popularity=0.5,   # Средняя популярность по умолчанию
                    vec=None,         # Пока без векторов
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                place_models.append(place)
                
            except Exception as e:
                logger.error(f"Error converting place {raw_place.get('name', 'Unknown')}: {e}")
                continue
        
        logger.info(f"Converted {len(place_models)} places to models")
        return place_models
    
    async def get_timeout_places_stats(self) -> Dict:
        """Get statistics about Timeout places in database."""
        try:
            # Получаем все места из Timeout
            timeout_places = await get_places_by_source('timeout_bangkok')
            
            # Группируем по категориям
            by_category = {}
            by_area = {}
            total_count = len(timeout_places)
            
            for place in timeout_places:
                # По категориям (флагам)
                for flag in place.flags:
                    if flag not in by_category:
                        by_category[flag] = 0
                    by_category[flag] += 1
                
                # По районам
                if place.area:
                    if place.area not in by_area:
                        by_area[place.area] = 0
                    by_area[place.area] += 1
            
            return {
                'total_places': total_count,
                'by_category': by_category,
                'by_area': by_area,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting Timeout places stats: {e}")
            return {
                'error': str(e),
                'total_places': 0,
                'by_category': {},
                'by_area': {},
                'last_updated': datetime.now().isoformat()
            }
    
    async def test_parser(self, category: str = "food_dining", limit: int = 3) -> Dict:
        """Test the parser with a small sample."""
        logger.info(f"Testing parser with category: {category}, limit: {limit}")
        
        if not self.parser:
            raise RuntimeError("Parser not initialized. Use async context manager.")
        
        try:
            # Тестируем на одной категории
            if category in self.parser.categories:
                url = self.parser.categories[category][0]  # Берем первый URL
                places = await self.parser.scrape_category(category, url)
                
                # Ограничиваем количество для теста
                test_places = places[:limit]
                
                return {
                    'success': True,
                    'category': category,
                    'url_tested': url,
                    'places_found': len(places),
                    'test_places': test_places,
                    'sample_data': [
                        {
                            'name': p.get('name'),
                            'description': p.get('description', '')[:100] + '...' if len(p.get('description', '')) > 100 else p.get('description', ''),
                            'area': p.get('area'),
                            'price_level': p.get('price_level'),
                            'flags': p.get('flags', [])
                        }
                        for p in test_places
                    ]
                }
            else:
                return {
                    'success': False,
                    'error': f"Unknown category: {category}",
                    'available_categories': list(self.parser.categories.keys())
                }
                
        except Exception as e:
            logger.error(f"Error testing parser: {e}")
            return {
                'success': False,
                'error': str(e),
                'category': category
            }


async def main():
    """Test function."""
    logging.basicConfig(level=logging.INFO)
    
    async with TimeoutPlacesService() as service:
        # Тестируем парсер
        print("Testing parser...")
        test_result = await service.test_parser("food_dining", 3)
        
        if test_result['success']:
            print(f"✅ Parser test successful!")
            print(f"Found {test_result['places_found']} places in category {test_result['category']}")
            print("\nSample places:")
            for i, place in enumerate(test_result['sample_data']):
                print(f"{i+1}. {place['name']}")
                print(f"   Area: {place['area']}")
                print(f"   Price: {place['price_level']}")
                print(f"   Flags: {place['flags']}")
                print()
        else:
            print(f"❌ Parser test failed: {test_result['error']}")
        
        # Получаем статистику
        print("Getting stats...")
        stats = await service.get_timeout_places_stats()
        print(f"Database stats: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
