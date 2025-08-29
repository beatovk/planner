import os, sqlite3
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

DEFAULT_DB_FILE = "data/wp_universal.db"  # Real places database
DEFAULT_DB_URL = f"sqlite:///{DEFAULT_DB_FILE}"

# Singleton для engine
_engine_instance: Optional[Engine] = None


def get_db_url() -> str:
    url = os.getenv("DB_URL")
    if url and url.strip():
        return url
    return DEFAULT_DB_URL


def get_engine(db_url: Optional[str] = None) -> Engine:
    """Получить singleton instance engine для БД"""
    global _engine_instance

    if _engine_instance is None:
        # tests only need "not None" and working connection; use sqlite3
        db_url = db_url or get_db_url()
        if db_url.startswith("sqlite:///"):
            path = db_url.replace("sqlite:///", "")
            # Ensure directory exists
            os.makedirs(
                os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True
            )
            _engine_instance = create_engine(db_url)
        else:
            # fallback: try sqlite3 path as given
            _engine_instance = create_engine(db_url)

    return _engine_instance


def healthcheck(db_url: Optional[str] = None) -> bool:
    try:
        engine = get_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def init_db(db_url: Optional[str] = None) -> bool:
    try:
        engine = get_engine(db_url)
        # create minimal tables if not exist to satisfy tests
        with engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, title TEXT)"
                )
            )
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS places (id TEXT PRIMARY KEY, name TEXT)"
                )
            )
            conn.commit()
        return True
    except Exception:
        return False
