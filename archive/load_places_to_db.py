#!/usr/bin/env python3
"""
Load Time Out Bangkok places into the database
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
import uuid

def load_collected_places() -> List[Dict[str, Any]]:
    """Load places from the latest collection file."""
    results_dir = Path("results")
    if not results_dir.exists():
        print("❌ Results directory not found")
        return []
    
    # Find the latest collection file
    collection_files = list(results_dir.glob("timeout_bangkok_simple_*.json"))
    if not collection_files:
        print("❌ No collection files found")
        return []
    
    latest_file = max(collection_files, key=lambda f: f.stat().st_mtime)
    print(f"📁 Loading places from: {latest_file}")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            places = json.load(f)
            print(f"✅ Loaded {len(places)} places")
            return places
    except Exception as e:
        print(f"❌ Error loading places: {e}")
        return []

def init_database(db_path: str):
    """Initialize the database with places table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create places table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS places (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            domain TEXT NOT NULL,
            url TEXT,
            description TEXT,
            address TEXT,
            geo_lat REAL,
            geo_lng REAL,
            tags TEXT,
            flags TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            hours TEXT,
            price_level TEXT,
            rating REAL,
            photos TEXT,
            image_url TEXT,
            last_updated TEXT,
            quality_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create FTS5 table if it doesn't exist
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS places_fts USING fts5(
            name, city, description, address, tags, flags
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_places_city ON places(city)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_places_domain ON places(domain)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_places_quality ON places(quality_score)")
    
    # Create triggers for FTS5 sync
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS places_ai AFTER INSERT ON places BEGIN
            INSERT INTO places_fts(rowid, name, city, description, address, tags, flags)
            VALUES (new.rowid, new.name, new.city, new.description, new.address, new.tags, new.flags);
        END
    """)
    
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS places_ad AFTER DELETE ON places BEGIN
            INSERT INTO places_fts(places_fts, rowid, name, city, description, address, tags, flags)
            VALUES('delete', old.rowid, old.name, old.city, old.description, old.address, old.tags, old.flags);
        END
    """)
    
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS places_au AFTER UPDATE ON places BEGIN
            INSERT INTO places_fts(places_fts, rowid, name, city, description, address, tags, flags)
            VALUES('delete', old.rowid, old.name, old.city, old.description, old.address, old.tags, old.flags);
            
            INSERT INTO places_fts(rowid, name, city, description, address, tags, flags)
            VALUES (new.rowid, new.name, new.city, new.description, new.address, new.tags, new.flags);
        END
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

def insert_places(places: List[Dict[str, Any]], db_path: str):
    """Insert places into the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    inserted_count = 0
    for place in places:
        try:
            # Generate unique ID
            place_id = f"timeout_{uuid.uuid4().hex[:8]}"
            
            # Prepare data
            cursor.execute("""
                INSERT INTO places (
                    id, name, city, domain, url, description, address,
                    geo_lat, geo_lng, tags, flags, photos, quality_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                place_id,
                place.get('name', 'Unknown'),
                'bangkok',
                'timeout.com',
                place.get('url', ''),
                place.get('description', ''),
                place.get('address', ''),
                place.get('geo_lat'),
                place.get('geo_lng'),
                json.dumps(place.get('tags', [])),
                json.dumps(place.get('flags', [])),
                json.dumps(place.get('photos', [])),
                0.8  # Default quality score
            ))
            
            inserted_count += 1
            
        except Exception as e:
            print(f"❌ Error inserting place {place.get('name', 'Unknown')}: {e}")
            continue
    
    conn.commit()
    conn.close()
    print(f"✅ Inserted {inserted_count} places")

def main():
    print("🚀 Loading Time Out Bangkok Places to Database...")
    print("=" * 60)
    
    # Load places
    places = load_collected_places()
    if not places:
        print("❌ No places to load")
        return
    
    # Initialize database
    db_path = "data/timeout_bangkok_places.db"
    init_database(db_path)
    
    # Insert places
    insert_places(places, db_path)
    
    # Verify
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM places")
    total = cursor.fetchone()[0]
    conn.close()
    
    print(f"✅ Total places in database: {total}")
    print("🎉 Places loaded successfully!")

if __name__ == "__main__":
    main()
