"""
Deduplication package for Bangkok Places Parser.
"""

from .dedup_engine import DedupEngine, DedupCandidate, create_dedup_engine

__all__ = [
    'DedupEngine',
    'DedupCandidate', 
    'create_dedup_engine'
]
