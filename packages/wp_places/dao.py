from sqlalchemy import text, Engine
from typing import List, Dict, Any
import json
from pathlib import Path


def init_schema(engine: Engine) -> None:
    """Инициализация схемы БД для мест"""
    with engine.connect() as conn:
        # Создаем таблицу places если не существует
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS places (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                city TEXT,
                address TEXT,
                tags TEXT,  -- JSON string
                flags TEXT,  -- JSON string
                typical_time TEXT,
                source TEXT,
                rating REAL,
                price_range TEXT,
                google_maps_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Создаем индексы для быстрого поиска
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_places_city ON places(city)"))
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_places_flags ON places(flags)")
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_places_rating ON places(rating)")
        )

        conn.commit()

        # Инициализируем FTS5
        try:
            from packages.wp_places.search import ensure_fts

            ensure_fts(engine)
        except Exception as e:
            print(f"Warning: FTS5 initialization failed: {e}")


def save_places(engine: Engine, items: List[Dict[str, Any]]) -> int:
    """Сохранение списка мест в БД"""
    if not items:
        return 0

    with engine.connect() as conn:
        # Подготавливаем данные для вставки
        for item in items:
            # Конвертируем списки в JSON строки
            tags_json = json.dumps(item.get("tags", []))
            flags_json = json.dumps(item.get("flags", []))

            # Проверяем существование записи
            existing = conn.execute(
                text("SELECT id FROM places WHERE id = :id"), {"id": item["id"]}
            ).fetchone()

            if existing:
                # Обновляем существующую запись
                conn.execute(
                    text(
                        """
                    UPDATE places SET
                        name = :name,
                        description = :description,
                        city = :city,
                        address = :address,
                        tags = :tags,
                        flags = :flags,
                        typical_time = :typical_time,
                        source = :source,
                        rating = :rating,
                        price_range = :price_range,
                        google_maps_url = :google_maps_url,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """
                    ),
                    {
                        "id": item["id"],
                        "name": item.get("name", ""),
                        "description": item.get("description", ""),
                        "city": item.get("city", ""),
                        "address": item.get("address", ""),
                        "tags": tags_json,
                        "flags": flags_json,
                        "typical_time": item.get("typical_time", ""),
                        "source": item.get("source", ""),
                        "rating": item.get("rating", 0.0),
                        "price_range": item.get("price_range", ""),
                        "google_maps_url": item.get("google_maps_url", ""),
                    },
                )
            else:
                # Вставляем новую запись
                conn.execute(
                    text(
                        """
                    INSERT INTO places (
                        id, name, description, city, address, tags, flags,
                        typical_time, source, rating, price_range, google_maps_url
                    ) VALUES (
                        :id, :name, :description, :city, :address, :tags, :flags,
                        :typical_time, :source, :rating, :price_range, :google_maps_url
                    )
                """
                    ),
                    {
                        "id": item["id"],
                        "name": item.get("name", ""),
                        "description": item.get("description", ""),
                        "city": item.get("city", ""),
                        "address": item.get("address", ""),
                        "tags": tags_json,
                        "flags": flags_json,
                        "typical_time": item.get("typical_time", ""),
                        "source": item.get("source", ""),
                        "rating": item.get("rating", 0.0),
                        "price_range": item.get("price_range", ""),
                        "google_maps_url": item.get("google_maps_url", ""),
                    },
                )

        conn.commit()

        # Переиндексируем FTS5 после изменений
        try:
            from packages.wp_places.search import reindex_fts

            reindex_fts(engine)
        except Exception as e:
            print(f"Warning: FTS5 reindex failed: {e}")

        return len(items)


def get_places_by_flags(
    engine: Engine, flags: List[str], limit: int = 50
) -> List[Dict[str, Any]]:
    """Получение мест по флагам"""
    if not flags:
        return []

    with engine.connect() as conn:
        # Создаем условие для поиска по флагам
        flag_conditions = []
        params = {}

        for i, flag in enumerate(flags):
            flag_conditions.append(f"flags LIKE :flag_{i}")
            params[f"flag_{i}"] = f"%{flag}%"

        where_clause = " OR ".join(flag_conditions)

        query = f"""
            SELECT * FROM places 
            WHERE {where_clause}
            ORDER BY rating DESC, name ASC
            LIMIT :limit
        """
        params["limit"] = limit

        result = conn.execute(text(query), params)
        places = []

        for row in result:
            place = dict(row._mapping)
            # Конвертируем JSON строки обратно в списки
            if place.get("tags"):
                try:
                    place["tags"] = json.loads(place["tags"])
                except:
                    place["tags"] = []
            if place.get("flags"):
                try:
                    place["flags"] = json.loads(place["flags"])
                except:
                    place["flags"] = []
            places.append(place)

        return places


def get_all_places(engine: Engine, limit: int = 200) -> List[Dict[str, Any]]:
    """Получение всех мест с лимитом"""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM places ORDER BY rating DESC, name ASC LIMIT :limit"),
            {"limit": limit},
        )
        places = []

        for row in result:
            place = dict(row._mapping)
            # Конвертируем JSON строки обратно в списки
            if place.get("tags"):
                try:
                    place["tags"] = json.loads(place["tags"])
                except:
                    place["tags"] = []
            if place.get("flags"):
                try:
                    place["flags"] = json.loads(place["flags"])
                except:
                    place["flags"] = []
            places.append(place)

        return places


def get_places_stats(engine: Engine) -> Dict[str, Any]:
    """Получение статистики по местам"""
    with engine.connect() as conn:
        # Общее количество мест
        total_result = conn.execute(text("SELECT COUNT(*) as total FROM places"))
        total = total_result.fetchone()["total"]

        # Количество по городам
        cities_result = conn.execute(
            text(
                """
            SELECT city, COUNT(*) as count 
            FROM places 
            GROUP BY city 
            ORDER BY count DESC
        """
            )
        )
        cities = {row["city"]: row["count"] for row in cities_result}

        # Средний рейтинг
        rating_result = conn.execute(
            text(
                """
            SELECT AVG(rating) as avg_rating 
            FROM places 
            WHERE rating > 0
        """
            )
        )
        avg_rating = rating_result.fetchone()["avg_rating"] or 0.0

        # Количество по флагам
        flags_result = conn.execute(
            text(
                """
            SELECT flags, COUNT(*) as count 
            FROM places 
            WHERE flags IS NOT NULL AND flags != '[]'
        """
            )
        )
        flags_stats = {}
        for row in flags_result:
            try:
                flags_list = json.loads(row["flags"])
                for flag in flags_list:
                    flags_stats[flag] = flags_stats.get(flag, 0) + 1
            except:
                continue

        return {
            "total_places": total,
            "cities": cities,
            "average_rating": round(avg_rating, 2),
            "flags_distribution": flags_stats,
        }


def load_from_json(engine: Engine, json_file_path: str) -> int:
    """Загрузка мест из JSON файла в БД"""
    try:
        json_path = Path(json_file_path)
        if not json_path.exists():
            return 0

        with open(json_path, "r", encoding="utf-8") as f:
            places_data = json.load(f)

        if isinstance(places_data, list):
            return save_places(engine, places_data)
        else:
            return 0

    except Exception as e:
        print(f"Error loading places from JSON: {e}")
        return 0
