"""
Search functionality for places using FTS5.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import text, Engine
import json
from pathlib import Path


def ensure_fts(engine: Engine) -> None:
    """Обеспечивает создание FTS5 таблиц и триггеров"""
    # Читаем SQL миграцию
    migration_file = Path(__file__).parent.parent.parent / "search" / "fts5_migrations.sql"
    
    if not migration_file.exists():
        raise FileNotFoundError(f"FTS5 migration file not found: {migration_file}")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    # Выполняем миграцию
    with engine.connect() as conn:
        # Разбиваем SQL на отдельные команды
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for statement in statements:
            if statement:
                try:
                    conn.execute(text(statement))
                except Exception as e:
                    # Игнорируем ошибки "уже существует"
                    if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                        print(f"Warning executing FTS5 migration: {e}")
        
        conn.commit()


def reindex_fts(engine: Engine) -> int:
    """Переиндексирует FTS5 таблицу"""
    with engine.connect() as conn:
        # Получаем количество записей в основной таблице
        result = conn.execute(text("SELECT COUNT(*) FROM places"))
        total_places = result.fetchone()[0]
        
        if total_places == 0:
            return 0
        
        # Очищаем FTS таблицу
        conn.execute(text("DELETE FROM places_fts"))
        
        # Переиндексируем все записи
        conn.execute(text("""
            INSERT INTO places_fts(rowid, title, description, tags, flags, city, address)
            SELECT id, name, description, tags, flags, city, address FROM places
        """))
        
        conn.commit()
        
        # Проверяем количество записей в FTS
        result = conn.execute(text("SELECT COUNT(*) FROM places_fts"))
        fts_count = result.fetchone()[0]
        
        return fts_count


def search(engine: Engine, query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Поиск мест с использованием FTS5 и BM25 ранжирования
    
    Args:
        engine: SQLAlchemy engine
        query: Поисковый запрос
        limit: Максимальное количество результатов
        
    Returns:
        Список мест с релевантностью
    """
    if not query.strip():
        return []
    
    with engine.connect() as conn:
        # Поиск с BM25 ранжированием
        # bm25(places_fts) возвращает оценку релевантности
        sql = text("""
            SELECT 
                p.*,
                bm25(places_fts) as rank
            FROM places p
            JOIN places_fts ON places_fts.rowid = p.id
            WHERE places_fts MATCH :query
            ORDER BY rank ASC, p.rating DESC
            LIMIT :limit
        """)
        
        result = conn.execute(sql, {"query": query, "limit": limit})
        places = []
        
        for row in result:
            place = dict(row._mapping)
            
            # Конвертируем JSON строки обратно в списки
            if place.get('tags'):
                try:
                    place['tags'] = json.loads(place['tags'])
                except:
                    place['tags'] = []
            if place.get('flags'):
                try:
                    place['flags'] = json.loads(place['flags'])
                except:
                    place['flags'] = []
            
            # Убираем служебные поля
            place.pop('rank', None)
            
            places.append(place)
        
        return places


def search_by_category(engine: Engine, query: str, category: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Поиск мест по категории с использованием FTS5
    
    Args:
        engine: SQLAlchemy engine
        query: Поисковый запрос
        category: Категория для фильтрации
        limit: Максимальное количество результатов
        
    Returns:
        Список мест с релевантностью
    """
    if not query.strip() or not category.strip():
        return []
    
    with engine.connect() as conn:
        # Поиск с фильтрацией по категории
        sql = text("""
            SELECT 
                p.*,
                bm25(places_fts) as rank
            FROM places p
            JOIN places_fts ON places_fts.rowid = p.id
            WHERE places_fts MATCH :query
                AND (p.flags LIKE :category OR p.tags LIKE :category)
            ORDER BY rank ASC, p.rating DESC
            LIMIT :limit
        """)
        
        category_pattern = f"%{category}%"
        result = conn.execute(sql, {
            "query": query, 
            "category": category_pattern, 
            "limit": limit
        })
        
        places = []
        for row in result:
            place = dict(row._mapping)
            
            # Конвертируем JSON строки обратно в списки
            if place.get('tags'):
                try:
                    place['tags'] = json.loads(place['tags'])
                except:
                    place['tags'] = []
            if place.get('flags'):
                try:
                    place['flags'] = json.loads(place['flags'])
                except:
                    place['flags'] = []
            
            # Убираем служебные поля
            place.pop('rank', None)
            
            places.append(place)
        
        return places


def get_search_stats(engine: Engine) -> Dict[str, Any]:
    """Получение статистики по FTS5 поиску"""
    with engine.connect() as conn:
        # Количество записей в FTS
        result = conn.execute(text("SELECT COUNT(*) FROM places_fts"))
        fts_count = result.fetchone()[0]
        
        # Количество записей в основной таблице
        result = conn.execute(text("SELECT COUNT(*) FROM places"))
        places_count = result.fetchone()[0]
        
        # Проверяем синхронизацию
        sync_status = "synced" if fts_count == places_count else "out_of_sync"
        
        return {
            "fts_records": fts_count,
            "places_records": places_count,
            "sync_status": sync_status,
            "fts_enabled": True
        }
