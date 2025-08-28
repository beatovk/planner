#!/usr/bin/env python3
"""
Database layer for places with SQLite and FTS5.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

from ..models.place import Place, PlaceCreate, PlaceUpdate, PlaceSearch

logger = logging.getLogger(__name__)


class PlacesDatabase:
    """Database manager for places with FTS5 support."""
    
    def __init__(self, db_path: str = "data/processed/places.db"):
        """Initialize database connection."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Создаем таблицы при инициализации
        self._create_tables()
        self._create_fts_index()
        self._create_triggers()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
        return conn
    
    def _create_tables(self):
        """Create main tables."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS places (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    city TEXT NOT NULL DEFAULT 'bangkok',
                    area TEXT,
                    address TEXT,
                    lat REAL,
                    lon REAL,
                    flags TEXT,  -- JSON array as string
                    tags TEXT,   -- JSON array as string
                    price_level INTEGER,
                    cuisine TEXT,
                    atmosphere TEXT,
                    image_url TEXT,
                    image_urls TEXT,  -- JSON array as string
                    phone TEXT,
                    website TEXT,
                    hours TEXT,
                    popularity REAL DEFAULT 0.5,
                    quality_score REAL DEFAULT 0.0,
                    extracted_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    version TEXT DEFAULT '1.0',
                    metadata TEXT,  -- JSON object as string
                    
                    -- Индексы для быстрого поиска
                    UNIQUE(source, source_url)
                )
            """)
            
            # Создаем индексы для быстрого поиска
            conn.execute("CREATE INDEX IF NOT EXISTS idx_places_city ON places(city)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_places_source ON places(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_places_area ON places(area)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_places_flags ON places(flags)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_places_price ON places(price_level)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_places_quality ON places(quality_score)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_places_extracted ON places(extracted_at)")
            
            logger.info("Main tables created successfully")
    
    def _create_fts_index(self):
        """Create FTS5 virtual table for full-text search."""
        with self._get_connection() as conn:
            # Создаем FTS5 таблицу
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS places_fts USING fts5(
                    name,
                    description,
                    area,
                    cuisine,
                    atmosphere,
                    tags,
                    content='places',
                    content_rowid='rowid'
                )
            """)
            
            logger.info("FTS5 index created successfully")
    
    def _create_triggers(self):
        """Create triggers for FTS5 synchronization."""
        with self._get_connection() as conn:
            # Триггер для INSERT
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS places_ai AFTER INSERT ON places BEGIN
                    INSERT INTO places_fts(rowid, name, description, area, cuisine, atmosphere, tags)
                    VALUES (
                        new.rowid,
                        new.name,
                        COALESCE(new.description, ''),
                        COALESCE(new.area, ''),
                        COALESCE(new.cuisine, ''),
                        COALESCE(new.atmosphere, ''),
                        COALESCE(new.tags, '')
                    );
                END
            """)
            
            # Триггер для UPDATE
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS places_au AFTER UPDATE ON places BEGIN
                    UPDATE places_fts SET
                        name = COALESCE(new.name, ''),
                        description = COALESCE(new.description, ''),
                        area = COALESCE(new.area, ''),
                        cuisine = COALESCE(new.cuisine, ''),
                        atmosphere = COALESCE(new.atmosphere, ''),
                        tags = COALESCE(new.tags, '')
                    WHERE rowid = new.rowid;
                END
            """)
            
            # Триггер для DELETE
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS places_ad AFTER DELETE ON places BEGIN
                    DELETE FROM places_fts WHERE rowid = old.rowid;
                END
            """)
            
            logger.info("Triggers created successfully")
    
    def insert_place(self, place: Place) -> bool:
        """Insert a new place."""
        try:
            with self._get_connection() as conn:
                place_dict = place.to_dict()
                
                # Подготавливаем данные для вставки
                place_dict['flags'] = json.dumps(place.flags) if place.flags else None
                place_dict['tags'] = json.dumps(place.tags) if place.tags else None
                place_dict['image_urls'] = json.dumps(place.image_urls) if place.image_urls else None
                place_dict['metadata'] = json.dumps(place.metadata) if place.metadata else None
                
                # Вставляем в основную таблицу
                conn.execute("""
                    INSERT OR REPLACE INTO places (
                        id, source, source_url, name, description, city, area, address,
                        lat, lon, flags, tags, price_level, cuisine, atmosphere,
                        image_url, image_urls, phone, website, hours, popularity,
                        quality_score, extracted_at, updated_at, version, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    place_dict['id'], place_dict['source'], place_dict['source_url'],
                    place_dict['name'], place_dict['description'], place_dict['city'],
                    place_dict['area'], place_dict['address'], place_dict['lat'],
                    place_dict['lon'], place_dict['flags'], place_dict['tags'],
                    place_dict['price_level'], place_dict['cuisine'], place_dict['atmosphere'],
                    place_dict['image_url'], place_dict['image_urls'], place_dict['phone'],
                    place_dict['website'], place_dict['hours'], place_dict['popularity'],
                    place_dict['quality_score'], place_dict['extracted_at'],
                    place_dict['updated_at'], place_dict['version'], place_dict['metadata']
                ))
                
                conn.commit()
                logger.info(f"Place inserted successfully: {place.name}")
                return True
                
        except Exception as e:
            logger.error(f"Error inserting place {place.name}: {e}")
            return False
    
    def insert_places(self, places: List[Place]) -> int:
        """Insert multiple places."""
        success_count = 0
        
        with self._get_connection() as conn:
            for place in places:
                try:
                    place_dict = place.to_dict()
                    
                    # Подготавливаем данные
                    place_dict['flags'] = json.dumps(place.flags) if place.flags else None
                    place_dict['tags'] = json.dumps(place.tags) if place.tags else None
                    place_dict['image_urls'] = json.dumps(place.image_urls) if place.image_urls else None
                    place_dict['metadata'] = json.dumps(place.metadata) if place.metadata else None
                    
                    # Вставляем
                    conn.execute("""
                        INSERT OR REPLACE INTO places (
                            id, source, source_url, name, description, city, area, address,
                            lat, lon, flags, tags, price_level, cuisine, atmosphere,
                            image_url, image_urls, phone, website, hours, popularity,
                            quality_score, extracted_at, updated_at, version, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        place_dict['id'], place_dict['source'], place_dict['source_url'],
                        place_dict['name'], place_dict['description'], place_dict['city'],
                        place_dict['area'], place_dict['address'], place_dict['lat'],
                        place_dict['lon'], place_dict['flags'], place_dict['tags'],
                        place_dict['price_level'], place_dict['cuisine'], place_dict['atmosphere'],
                        place_dict['image_url'], place_dict['image_urls'], place_dict['phone'],
                        place_dict['website'], place_dict['hours'], place_dict['popularity'],
                        place_dict['quality_score'], place_dict['extracted_at'],
                        place_dict['updated_at'], place_dict['version'], place_dict['metadata']
                    ))
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Error inserting place {place.name}: {e}")
                    continue
            
            conn.commit()
        
        logger.info(f"Inserted {success_count}/{len(places)} places successfully")
        return success_count
    
    def get_place_by_id(self, place_id: str) -> Optional[Place]:
        """Get place by ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT * FROM places WHERE id = ?", (place_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_place(dict(row))
                return None
                
        except Exception as e:
            logger.error(f"Error getting place {place_id}: {e}")
            return None
    
    def get_places_by_source(self, source: str, limit: int = 100) -> List[Place]:
        """Get places by source."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM places WHERE source = ? ORDER BY extracted_at DESC LIMIT ?",
                    (source, limit)
                )
                
                places = []
                for row in cursor.fetchall():
                    places.append(self._row_to_place(dict(row)))
                
                return places
                
        except Exception as e:
            logger.error(f"Error getting places by source {source}: {e}")
            return []
    
    def search_places(self, search_query: PlaceSearch) -> Tuple[List[Place], int]:
        """Search places using FTS5 and filters."""
        try:
            with self._get_connection() as conn:
                # Базовый SQL запрос
                sql_parts = ["SELECT p.* FROM places p"]
                params = []
                
                # FTS5 поиск если есть query
                if search_query.query and search_query.query.strip():
                    sql_parts.append("JOIN places_fts fts ON p.rowid = fts.rowid")
                    sql_parts.append("WHERE places_fts MATCH ?")
                    params.append(search_query.query)
                else:
                    sql_parts.append("WHERE 1=1")
                
                # Фильтры
                if search_query.flags:
                    placeholders = ','.join(['?' for _ in search_query.flags])
                    sql_parts.append(f"AND p.flags LIKE '%' || ? || '%'")
                    params.extend(search_query.flags)
                
                if search_query.area:
                    sql_parts.append("AND p.area = ?")
                    params.append(search_query.area)
                
                if search_query.price_level:
                    sql_parts.append("AND p.price_level = ?")
                    params.append(search_query.price_level.value)
                
                if search_query.cuisine:
                    sql_parts.append("AND p.cuisine = ?")
                    params.append(search_query.cuisine)
                
                # Сортировка
                order_by = "ORDER BY "
                if search_query.sort_by == "relevance" and search_query.query:
                    order_by += "bm25(places_fts) DESC"
                elif search_query.sort_by == "quality":
                    order_by += "p.quality_score DESC"
                elif search_query.sort_by == "popularity":
                    order_by += "p.popularity DESC"
                elif search_query.sort_by == "name":
                    order_by += "p.name ASC"
                else:
                    order_by += "p.updated_at DESC"
                
                if search_query.sort_order == "asc":
                    order_by = order_by.replace(" DESC", " ASC").replace(" ASC", " ASC")
                
                sql_parts.append(order_by)
                
                # Лимит и смещение
                sql_parts.append("LIMIT ? OFFSET ?")
                params.extend([search_query.limit, search_query.offset])
                
                # Выполняем запрос
                sql = " ".join(sql_parts)
                cursor = conn.execute(sql, params)
                
                # Получаем результаты
                places = []
                for row in cursor.fetchall():
                    places.append(self._row_to_place(dict(row)))
                
                # Получаем общее количество
                count_sql = " ".join(sql_parts[:-2])  # Без LIMIT и OFFSET
                count_sql = count_sql.replace("SELECT p.*", "SELECT COUNT(*)")
                
                cursor = conn.execute(count_sql, params[:-2])
                total = cursor.fetchone()[0]
                
                return places, total
                
        except Exception as e:
            logger.error(f"Error searching places: {e}")
            return [], 0
    
    def update_place(self, place_id: str, update_data: PlaceUpdate) -> bool:
        """Update existing place."""
        try:
            with self._get_connection() as conn:
                # Подготавливаем данные для обновления
                update_dict = update_data.dict(exclude_unset=True)
                
                if 'flags' in update_dict and update_dict['flags']:
                    update_dict['flags'] = json.dumps(update_dict['flags'])
                
                if 'tags' in update_dict and update_dict['tags']:
                    update_dict['tags'] = json.dumps(update_dict['tags'])
                
                if 'image_urls' in update_dict and update_dict['image_urls']:
                    update_dict['image_urls'] = json.dumps(update_dict['image_urls'])
                
                if 'metadata' in update_dict and update_dict['metadata']:
                    update_dict['metadata'] = json.dumps(update_dict['metadata'])
                
                # Добавляем время обновления
                update_dict['updated_at'] = datetime.now().isoformat()
                
                # Строим SQL для UPDATE
                set_clause = ", ".join([f"{k} = ?" for k in update_dict.keys()])
                sql = f"UPDATE places SET {set_clause} WHERE id = ?"
                
                # Выполняем обновление
                params = list(update_dict.values()) + [place_id]
                conn.execute(sql, params)
                conn.commit()
                
                logger.info(f"Place updated successfully: {place_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating place {place_id}: {e}")
            return False
    
    def delete_place(self, place_id: str) -> bool:
        """Delete place by ID."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM places WHERE id = ?", (place_id,))
                conn.commit()
                
                logger.info(f"Place deleted successfully: {place_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting place {place_id}: {e}")
            return False
    
    def get_places_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with self._get_connection() as conn:
                stats = {}
                
                # Общее количество мест
                cursor = conn.execute("SELECT COUNT(*) FROM places")
                stats['total_places'] = cursor.fetchone()[0]
                
                # По источникам
                cursor = conn.execute("SELECT source, COUNT(*) FROM places GROUP BY source")
                stats['by_source'] = dict(cursor.fetchall())
                
                # По городам
                cursor = conn.execute("SELECT city, COUNT(*) FROM places GROUP BY city")
                stats['by_city'] = dict(cursor.fetchall())
                
                # По районам
                cursor = conn.execute("SELECT area, COUNT(*) FROM places WHERE area IS NOT NULL GROUP BY area ORDER BY COUNT(*) DESC LIMIT 10")
                stats['by_area'] = dict(cursor.fetchall())
                
                # По категориям (флагам)
                cursor = conn.execute("SELECT flags FROM places WHERE flags IS NOT NULL")
                flag_counts = {}
                for row in cursor.fetchall():
                    if row[0]:
                        try:
                            flags = json.loads(row[0])
                            for flag in flags:
                                flag_counts[flag] = flag_counts.get(flag, 0) + 1
                        except json.JSONDecodeError:
                            continue
                
                stats['by_flags'] = dict(sorted(flag_counts.items(), key=lambda x: x[1], reverse=True))
                
                # По качеству
                cursor = conn.execute("SELECT AVG(quality_score) FROM places WHERE quality_score > 0")
                stats['avg_quality_score'] = cursor.fetchone()[0] or 0.0
                
                # По датам
                cursor = conn.execute("SELECT MIN(extracted_at), MAX(extracted_at) FROM places")
                date_range = cursor.fetchone()
                stats['date_range'] = {
                    'earliest': date_range[0],
                    'latest': date_range[1]
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def _row_to_place(self, row: Dict[str, Any]) -> Place:
        """Convert database row to Place object."""
        # Обрабатываем JSON поля
        if row.get('flags'):
            try:
                row['flags'] = json.loads(row['flags'])
            except json.JSONDecodeError:
                row['flags'] = []
        
        if row.get('tags'):
            try:
                row['tags'] = json.loads(row['tags'])
            except json.JSONDecodeError:
                row['tags'] = []
        
        if row.get('image_urls'):
            try:
                row['image_urls'] = json.loads(row['image_urls'])
            except json.JSONDecodeError:
                row['image_urls'] = []
        
        if row.get('metadata'):
            try:
                row['metadata'] = json.loads(row['metadata'])
            except json.JSONDecodeError:
                row['metadata'] = {}
        
        return Place.from_dict(row)
    
    def rebuild_fts_index(self) -> bool:
        """Rebuild FTS5 index."""
        try:
            with self._get_connection() as conn:
                # Удаляем старый индекс
                conn.execute("DROP TABLE IF EXISTS places_fts")
                
                # Создаем новый
                self._create_fts_index()
                self._create_triggers()
                
                # Переиндексируем существующие данные
                conn.execute("""
                    INSERT INTO places_fts(rowid, name, description, area, cuisine, atmosphere, tags)
                    SELECT 
                        rowid,
                        COALESCE(name, ''),
                        COALESCE(description, ''),
                        COALESCE(area, ''),
                        COALESCE(cuisine, ''),
                        COALESCE(atmosphere, ''),
                        COALESCE(tags, '')
                    FROM places
                """)
                
                conn.commit()
                logger.info("FTS5 index rebuilt successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error rebuilding FTS5 index: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        # SQLite автоматически закрывает соединения
        pass
