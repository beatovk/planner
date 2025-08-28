"""
Geo Validator Agent

Агент-геовалидатор для проверки и исправления координат у существующих мест.
Интегрирован в мультиагентную систему Week Planner.

Задачи:
- Геокодинг адресов через Google Maps
- Проверка, что место в нужном городе/районе
- Расчет расстояний между местами
- Получение цен из Google Maps
- Генерация ссылок на конкретные места в Google Maps
- Сбор расширенных данных без API (рейтинги, цены, отзывы, часы работы)
- Результат: Точные координаты, ссылки и расширенная информация для всех мест
"""

import asyncio
import logging
import re
import json
import sqlite3
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import aiohttp
from urllib.parse import quote, urlencode

# Абсолютные импорты
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from packages.wp_agents.base import BaseAgent, AgentContext, AgentResult, AgentPriority, AgentStatus


@dataclass
class GeoValidatedPlace:
    """Место после геовалидации"""
    id: str
    name: str
    address: Optional[str] = None
    geo_lat: Optional[float] = None
    geo_lng: Optional[float] = None
    google_maps_url: Optional[str] = None
    city_validated: bool = False
    district_validated: bool = False
    price_level: Optional[str] = None
    google_rating: Optional[float] = None
    google_reviews: Optional[int] = None
    distance_from_center: Optional[float] = None
    # Новые поля для расширенных данных
    scraped_rating: Optional[float] = None
    scraped_reviews_count: Optional[int] = None
    scraped_price_level: Optional[str] = None
    opening_hours: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    category: Optional[str] = None
    features: Optional[List[str]] = None
    popular_hours: Optional[str] = None
    scraped_address: Optional[str] = None
    validated_at: str = ""
    raw_data: Dict[str, Any] = None


class GeoValidatorAgent(BaseAgent):
    """
    Агент-геовалидатор для проверки и исправления координат у существующих мест
    
    Функции согласно требованиям:
    1. Геокодинг адресов через Google Maps
    2. Проверка, что место в нужном городе/районе
    3. Расчет расстояний между местами
    4. Получение цен из Google Maps
    5. Генерация ссылок на конкретные места в Google Maps
    6. Сбор расширенных данных без API (рейтинги, цены, отзывы, часы работы)
    7. Результат: Точные координаты, ссылки и расширенная информация для всех мест
    """
    
    def __init__(self, db_path: str = "data/wp.db", google_api_key: Optional[str] = None):
        super().__init__(
            name="geo_validator",
            version="2.2.0",
            priority=AgentPriority.HIGH,
            feature_flag="WP_AGENTS_STAGE1_ENABLED"
        )
        self.logger = logging.getLogger("agent.geo_validator")
        self.db_path = db_path
        self.google_api_key = google_api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        
        # Центр Бангкока (примерные координаты)
        self.bangkok_center = {
            'lat': 13.7563,
            'lng': 100.5018
        }
        
        # Районы Бангкока с координатами
        self.bangkok_districts = {
            'sukhumvit': {'lat': 13.7380, 'lng': 100.5870, 'radius': 0.05},
            'silom': {'lat': 13.7246, 'lng': 100.5329, 'radius': 0.03},
            'siam': {'lat': 13.7466, 'lng': 100.5347, 'radius': 0.02},
            'pratunam': {'lat': 13.7539, 'lng': 100.5394, 'radius': 0.02},
            'yaowarat': {'lat': 13.7417, 'lng': 100.5075, 'radius': 0.03},
            'thonglor': {'lat': 13.7234, 'lng': 100.5834, 'radius': 0.03},
            'ari': {'lat': 13.7649, 'lng': 100.6443, 'radius': 0.03},
            'charoenkrung': {'lat': 13.7246, 'lng': 100.5075, 'radius': 0.04},
            'asoke': {'lat': 13.7373, 'lng': 100.5603, 'radius': 0.02},
            'iconsiam': {'lat': 13.7266, 'lng': 100.5133, 'radius': 0.02}
        }
        
        # Настройка сессии для HTTP-запросов
        self.session = None

    async def _execute_agent(self, context: AgentContext) -> AgentResult:
        """Основной метод выполнения агента"""
        try:
            self.logger.info("Запуск Geo Validator Agent")
            self.status = AgentStatus.RUNNING
            
            # Инициализируем сессию
            self.session = aiohttp.ClientSession()
            
            # Получаем места для валидации
            places = await self._get_places_for_validation()
            
            if not places:
                return AgentResult(
                    success=False,
                    error="Нет мест для валидации",
                    data={}
                )
            
            self.logger.info(f"Найдено {len(places)} мест для валидации")
            
            # Валидируем места
            validated_places = []
            errors = []
            
            for i, place in enumerate(places):
                try:
                    self.logger.info(f"Валидация места {i+1}/{len(places)}: {place.get('name', 'Unknown')}")
                    
                    validated_place = await self._validate_place(place)
                    if validated_place:
                        validated_places.append(validated_place)
                    else:
                        errors.append(f"Не удалось валидировать {place.get('name', 'Unknown')}")
                        
                except Exception as e:
                    error_msg = f"Ошибка валидации {place.get('name', 'Unknown')}: {e}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
            
            # Сохраняем результаты
            saved_count = await self._save_validated_places(validated_places)
            
            # Закрываем сессию
            if self.session:
                await self.session.close()
            
            self.status = AgentStatus.COMPLETED
            
            return AgentResult(
                success=True,
                data={
                    'places_processed': len(places),
                    'validated_places': len(validated_places),
                    'coordinates_updated': saved_count,
                    'maps_urls_created': len([p for p in validated_places if p.google_maps_url]),
                    'extended_data_collected': len([p for p in validated_places if p.scraped_rating or p.scraped_price_level]),
                    'errors': errors
                }
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка выполнения агента: {e}")
            self.status = AgentStatus.FAILED
            
            if self.session:
                await self.session.close()
            
            return AgentResult(
                success=False,
                error=str(e),
                data={}
            )

    async def _get_places_for_validation(self) -> List[Dict[str, Any]]:
        """Получает места для валидации из базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, address, geo_lat, geo_lng, 
                       price_level, rating, last_updated
                FROM places
                ORDER BY name
            """)
            
            places = []
            for row in cursor.fetchall():
                place = {
                    'id': row[0],
                    'name': row[1],
                    'address': row[2],
                    'geo_lat': row[3],
                    'geo_lng': row[4],
                    'price_level': row[5],
                    'rating': row[6],
                    'last_updated': row[7]
                }
                places.append(place)
            
            conn.close()
            return places
            
        except Exception as e:
            self.logger.error(f"Ошибка получения мест из базы данных: {e}")
            return []

    async def _validate_place(self, place: Dict[str, Any]) -> Optional[GeoValidatedPlace]:
        """Валидирует одно место"""
        try:
            # 1. Геокодинг адреса
            coordinates = await self._geocode_address(place['name'], place['address'])
            
            if not coordinates:
                self.logger.warning(f"Не удалось получить координаты для {place['name']}")
                return None
            
            # 2. Валидация города и района
            city_validated = self._validate_city(coordinates)
            district_validated = self._validate_district(coordinates)
            
            # 3. Расчет расстояния от центра
            distance_from_center = self._calculate_distance_from_center(coordinates)
            
            # 4. Получение данных из Google Maps (если есть API ключ)
            google_data = await self._get_google_maps_data(place['name'], coordinates)
            
            # 5. Сбор расширенных данных без API (рейтинг, цены, отзывы)
            scraped_data = await self._scrape_google_maps_data(place['name'], place['address'])
            
            # 6. Получение точной ссылки на Google Maps (без API)
            google_maps_url = await self._get_google_maps_place_url(place['name'], place['address'])
            
            # Если точная ссылка не найдена, генерируем поисковую
            if not google_maps_url:
                google_maps_url = self._generate_google_maps_url(place['name'], coordinates, place['address'])
            
            # 7. Создание валидированного места
            validated_place = GeoValidatedPlace(
                id=place['id'],
                name=place['name'],
                address=place['address'],
                geo_lat=coordinates['lat'],
                geo_lng=coordinates['lng'],
                google_maps_url=google_maps_url,
                city_validated=city_validated,
                district_validated=district_validated,
                price_level=google_data.get('price_level') or place.get('price_level'),
                google_rating=google_data.get('rating'),
                google_reviews=google_data.get('reviews'),
                distance_from_center=distance_from_center,
                # Новые поля для расширенных данных
                scraped_rating=scraped_data.get('rating'),
                scraped_reviews_count=scraped_data.get('reviews_count'),
                scraped_price_level=scraped_data.get('price_level'),
                opening_hours=scraped_data.get('opening_hours'),
                phone=scraped_data.get('phone'),
                website=scraped_data.get('website'),
                category=scraped_data.get('category'),
                features=scraped_data.get('features'),
                popular_hours=scraped_data.get('popular_hours'),
                scraped_address=scraped_data.get('scraped_address'),
                validated_at=datetime.now().isoformat(),
                raw_data=place
            )
            
            return validated_place
            
        except Exception as e:
            self.logger.error(f"Ошибка валидации места {place.get('name', 'Unknown')}: {e}")
            return None

    async def _geocode_address(self, name: str, address: Optional[str]) -> Optional[Dict[str, float]]:
        """Геокодирует адрес через Google Maps API или альтернативные методы"""
        
        # Если есть Google API ключ, используем официальный API
        if self.google_api_key:
            return await self._geocode_with_google_api(name, address)
        
        # Иначе используем альтернативные методы
        return await self._geocode_with_alternative_methods(name, address)

    async def _geocode_with_google_api(self, name: str, address: Optional[str]) -> Optional[Dict[str, float]]:
        """Геокодирование через официальный Google Maps API"""
        try:
            # Формируем поисковый запрос
            query = f"{name}, {address}" if address else name
            query += ", Bangkok, Thailand"
            
            # URL для Google Geocoding API
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': query,
                'key': self.google_api_key,
                'region': 'th'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                if data.get('status') == 'OK' and data.get('results'):
                    location = data['results'][0]['geometry']['location']
                    return {
                        'lat': location['lat'],
                        'lng': location['lng']
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка геокодирования через Google API: {e}")
            return None

    async def _geocode_with_alternative_methods(self, name: str, address: Optional[str]) -> Optional[Dict[str, float]]:
        """Геокодирование через альтернативные методы (без API ключа)"""
        try:
            # Метод 1: Поиск по названию места в известных районах
            coordinates = self._find_coordinates_by_name_and_district(name, address)
            if coordinates:
                return coordinates
            
            # Метод 2: Используем существующие координаты, если они есть
            if hasattr(self, 'raw_data') and self.raw_data:
                raw_data = self.raw_data
                if raw_data.get('geo_lat') and raw_data.get('geo_lng'):
                    return {
                        'lat': raw_data['geo_lat'],
                        'lng': raw_data['geo_lng']
                    }
            
            # Метод 3: Возвращаем центр Бангкока как fallback
            return self.bangkok_center
            
        except Exception as e:
            self.logger.error(f"Ошибка альтернативного геокодирования: {e}")
            return self.bangkok_center

    def _find_coordinates_by_name_and_district(self, name: str, address: Optional[str]) -> Optional[Dict[str, float]]:
        """Находит координаты по названию и району"""
        name_lower = name.lower()
        address_lower = (address or "").lower()
        
        # Определяем район по названию или адресу
        for district, district_info in self.bangkok_districts.items():
            if (district in name_lower or 
                district in address_lower or
                any(keyword in name_lower for keyword in district_info.get('keywords', []))):
                return district_info
        
        # Если не определили район, возвращаем центр Бангкока
        return self.bangkok_center

    def _validate_city(self, coordinates: Dict[str, float]) -> bool:
        """Проверяет, что место находится в Бангкоке"""
        # Простая проверка: координаты должны быть в пределах Бангкока
        bangkok_bounds = {
            'min_lat': 13.5,
            'max_lat': 14.0,
            'min_lng': 100.3,
            'max_lng': 100.8
        }
        
        return (
            bangkok_bounds['min_lat'] <= coordinates['lat'] <= bangkok_bounds['max_lat'] and
            bangkok_bounds['min_lng'] <= coordinates['lng'] <= bangkok_bounds['max_lng']
        )

    def _validate_district(self, coordinates: Dict[str, float]) -> bool:
        """Проверяет, что место находится в известном районе Бангкока"""
        for district, district_info in self.bangkok_districts.items():
            distance = self._calculate_distance(
                coordinates['lat'], coordinates['lng'],
                district_info['lat'], district_info['lng']
            )
            if distance <= district_info['radius']:
                return True
        return False

    def _calculate_distance_from_center(self, coordinates: Dict[str, float]) -> float:
        """Рассчитывает расстояние от центра Бангкока"""
        return self._calculate_distance(
            coordinates['lat'], coordinates['lng'],
            self.bangkok_center['lat'], self.bangkok_center['lng']
        )

    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Рассчитывает расстояние между двумя точками (в градусах)"""
        import math
        return math.sqrt((lat2 - lat1) ** 2 + (lng2 - lng1) ** 2)

    def _generate_google_maps_url(self, name: str, coordinates: Dict[str, float], address: Optional[str] = None) -> str:
        """Генерирует ссылку на конкретное место в Google Maps"""
        try:
            # Формируем поисковый запрос для точного поиска
            query_parts = [name]
            if address:
                query_parts.append(address)
            query_parts.append("Bangkok, Thailand")
            
            # Кодируем запрос для URL
            query = quote(" ".join(query_parts))
            
            # Создаем ссылку на Google Maps с координатами и поисковым запросом
            maps_url = f"https://www.google.com/maps/search/?api=1&query={query}"
            
            # Добавляем координаты для точного позиционирования
            if coordinates and coordinates.get('lat') and coordinates.get('lng'):
                maps_url += f"&ll={coordinates['lat']},{coordinates['lng']}"
            
            return maps_url
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации ссылки Google Maps: {e}")
            # Возвращаем базовую ссылку на поиск по названию
            return f"https://www.google.com/maps/search/?api=1&query={quote(name + ', Bangkok, Thailand')}"

    async def _get_google_maps_place_url(self, name: str, address: Optional[str] = None) -> Optional[str]:
        """
        Получает точную ссылку на заведение в Google Maps через веб-поиск (без API)
        Возвращает ссылку вида: https://www.google.com/maps/place/[PLACE_ID]
        """
        try:
            if not self.session:
                return None
            
            # Формируем поисковый запрос
            search_query = f"{name}"
            if address and address.strip():
                search_query += f" {address}"
            search_query += " Bangkok Thailand"
            
            # URL для поиска в Google Maps
            search_url = "https://www.google.com/maps/search/"
            params = {
                'q': search_query,
                'hl': 'en'  # Английский язык
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with self.session.get(search_url, params=params, headers=headers) as response:
                if response.status != 200:
                    return None
                
                html_content = await response.text()
                
                # Ищем Place ID в HTML
                place_id_match = re.search(r'place_id=([A-Za-z0-9_-]+)', html_content)
                if place_id_match:
                    place_id = place_id_match.group(1)
                    # Создаем прямую ссылку на место
                    place_url = f"https://www.google.com/maps/place/{place_id}"
                    self.logger.info(f"Найден Place ID для {name}: {place_id}")
                    return place_url
                
                # Если Place ID не найден, ищем ссылку на место
                place_link_match = re.search(r'href="(/maps/place/[^"]+)"', html_content)
                if place_link_match:
                    place_path = place_link_match.group(1)
                    place_url = f"https://www.google.com{place_path}"
                    self.logger.info(f"Найдена ссылка на место для {name}: {place_url}")
                    return place_url
                
                self.logger.warning(f"Place ID не найден для {name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка получения ссылки на место Google Maps для {name}: {e}")
            return None

    async def _scrape_google_maps_data(self, name: str, address: Optional[str] = None) -> Dict[str, Any]:
        """
        Собирает расширенные данные из Google Maps без API:
        - Рейтинг и отзывы
        - Ценовой уровень
        - Часы работы
        - Телефон, веб-сайт
        - Категории и особенности
        """
        try:
            if not self.session:
                return {}
            
            # Формируем поисковый запрос
            search_query = f"{name}"
            if address and address.strip():
                search_query += f" {address}"
            search_query += " Bangkok Thailand"
            
            # URL для поиска в Google Maps
            search_url = "https://www.google.com/maps/search/"
            params = {
                'q': search_query,
                'hl': 'en'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with self.session.get(search_url, params=params, headers=headers) as response:
                if response.status != 200:
                    return {}
                
                html_content = await response.text()
                
                # Извлекаем данные
                scraped_data = {}
                
                # 1. Рейтинг
                rating_match = re.search(r'(\d+\.?\d*)\s*stars?', html_content, re.IGNORECASE)
                if rating_match:
                    scraped_data['rating'] = float(rating_match.group(1))
                
                # Альтернативный поиск рейтинга
                rating_match2 = re.search(r'(\d+\.?\d*)\s*out of\s*5', html_content, re.IGNORECASE)
                if rating_match2:
                    scraped_data['rating'] = float(rating_match2.group(1))
                
                # 2. Количество отзывов
                reviews_match = re.search(r'(\d+(?:,\d+)*)\s*reviews?', html_content, re.IGNORECASE)
                if reviews_match:
                    reviews_str = reviews_match.group(1).replace(',', '')
                    scraped_data['reviews_count'] = int(reviews_str)
                
                # 3. Ценовой уровень
                price_match = re.search(r'(\$+)\s*', html_content)
                if price_match:
                    price_level = len(price_match.group(1))
                    scraped_data['price_level'] = self._map_google_price_level(price_level)
                
                # 4. Часы работы
                hours_match = re.search(r'Open\s*(\d{1,2}:\d{2}\s*(?:AM|PM))\s*-\s*(\d{1,2}:\d{2}\s*(?:AM|PM))', html_content, re.IGNORECASE)
                if hours_match:
                    scraped_data['opening_hours'] = f"{hours_match.group(1)} - {hours_match.group(2)}"
                
                # 5. Телефон
                phone_match = re.search(r'(\+\d{1,3}\s*\d{1,4}\s*\d{1,4}\s*\d{1,4})', html_content)
                if phone_match:
                    scraped_data['phone'] = phone_match.group(1)
                
                # 6. Веб-сайт
                website_match = re.search(r'https?://[^\s<>"]+', html_content)
                if website_match:
                    scraped_data['website'] = website_match.group(0)
                
                # 7. Категория
                category_match = re.search(r'(restaurant|cafe|bar|coffee shop|bakery)', html_content, re.IGNORECASE)
                if category_match:
                    scraped_data['category'] = category_match.group(1).lower()
                
                # 8. Особенности
                features = []
                feature_keywords = ['outdoor seating', 'parking', 'wifi', 'delivery', 'takeout', 'reservations']
                for keyword in feature_keywords:
                    if re.search(keyword, html_content, re.IGNORECASE):
                        features.append(keyword)
                
                if features:
                    scraped_data['features'] = features
                
                # 9. Популярные часы
                popular_hours_match = re.search(r'Popular\s*times\s*([^<]+)', html_content, re.IGNORECASE)
                if popular_hours_match:
                    scraped_data['popular_hours'] = popular_hours_match.group(1).strip()
                
                # 10. Адрес (если не был передан)
                if not address:
                    address_match = re.search(r'Address[:\s]+([^<]+)', html_content, re.IGNORECASE)
                    if address_match:
                        scraped_data['scraped_address'] = address_match.group(1).strip()
                
                self.logger.info(f"Собрано данных для {name}: {len(scraped_data)} полей")
                return scraped_data
                
        except Exception as e:
            self.logger.error(f"Ошибка сбора данных Google Maps для {name}: {e}")
            return {}

    async def _get_google_maps_data(self, name: str, coordinates: Dict[str, float]) -> Dict[str, Any]:
        """Получает данные из Google Maps (рейтинг, отзывы, цены)"""
        if not self.google_api_key:
            return {}
        
        try:
            # Используем Places API для получения детальной информации
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                'location': f"{coordinates['lat']},{coordinates['lng']}",
                'radius': '100',  # 100 метров
                'name': name,
                'key': self.google_api_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return {}
                
                data = await response.json()
                
                if data.get('status') == 'OK' and data.get('results'):
                    place = data['results'][0]
                    
                    return {
                        'rating': place.get('rating'),
                        'reviews': place.get('user_ratings_total'),
                        'price_level': self._map_google_price_level(place.get('price_level'))
                    }
                
                return {}
                
        except Exception as e:
            self.logger.error(f"Ошибка получения данных из Google Maps: {e}")
            return {}

    def _map_google_price_level(self, google_price_level: Optional[int]) -> Optional[str]:
        """Маппит ценовой уровень Google на наш формат"""
        if google_price_level is None:
            return None
        
        price_mapping = {
            0: 'budget',
            1: 'budget',
            2: 'mid_range',
            3: 'mid_range',
            4: 'high_end'
        }
        
        return price_mapping.get(google_price_level, 'mid_range')

    async def _save_validated_places(self, validated_places: List[GeoValidatedPlace]) -> int:
        """Сохраняет валидированные места в базу данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Добавляем новые поля в таблицу, если их нет
            try:
                cursor.execute("ALTER TABLE places ADD COLUMN scraped_rating REAL")
            except:
                pass  # Поле уже существует
            
            try:
                cursor.execute("ALTER TABLE places ADD COLUMN scraped_reviews_count INTEGER")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE places ADD COLUMN scraped_price_level TEXT")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE places ADD COLUMN opening_hours TEXT")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE places ADD COLUMN phone TEXT")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE places ADD COLUMN website TEXT")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE places ADD COLUMN category TEXT")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE places ADD COLUMN features TEXT")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE places ADD COLUMN popular_hours TEXT")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE places ADD COLUMN scraped_address TEXT")
            except:
                pass
            
            saved_count = 0
            
            for place in validated_places:
                try:
                    # Обновляем существующее место
                    cursor.execute("""
                        UPDATE places SET
                            geo_lat = ?,
                            geo_lng = ?,
                            google_maps_url = ?,
                            price_level = ?,
                            rating = ?,
                            scraped_rating = ?,
                            scraped_reviews_count = ?,
                            scraped_price_level = ?,
                            opening_hours = ?,
                            phone = ?,
                            website = ?,
                            category = ?,
                            features = ?,
                            popular_hours = ?,
                            scraped_address = ?,
                            last_updated = ?
                        WHERE id = ?
                    """, (
                        place.geo_lat,
                        place.geo_lng,
                        place.google_maps_url,
                        place.price_level,
                        place.google_rating,
                        place.scraped_rating,
                        place.scraped_reviews_count,
                        place.scraped_price_level,
                        place.opening_hours,
                        place.phone,
                        place.website,
                        place.category,
                        json.dumps(place.features) if place.features else None,
                        place.popular_hours,
                        place.scraped_address,
                        datetime.now().isoformat(),
                        place.id
                    ))
                    
                    saved_count += 1
                    self.logger.info(f"Обновлено место: {place.name} (lat: {place.geo_lat}, lng: {place.geo_lng})")
                    
                except Exception as e:
                    self.logger.error(f"Ошибка обновления места {place.name}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            return saved_count
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения валидированных мест: {e}")
            return 0

    def can_execute(self, context: AgentContext) -> bool:
        """Проверяет, может ли агент выполниться"""
        return (
            self.is_enabled() and
            context.city and
            self.status != AgentStatus.RUNNING
        )

    def _validate_context(self, context: AgentContext) -> bool:
        """Валидирует контекст выполнения"""
        return bool(context.city)
