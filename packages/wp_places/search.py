"""
Search functionality for places.
"""

from typing import List, Optional


class SearchResult:
    """Search result for places."""
    
    def __init__(self, id: str, score: float, title: str):
        self.id = id
        self.score = score
        self.title = title


class FTS5Engine:
    """FTS5 search engine for places."""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
    
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search places by query."""
        # Mock implementation
        return []


def create_fts5_engine(db_url: Optional[str] = None) -> FTS5Engine:
    """Create FTS5 search engine."""
    db_url = db_url or "data/places.db"
    return FTS5Engine(db_url)
