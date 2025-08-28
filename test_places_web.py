#!/usr/bin/env python3
"""
Simple test server for places web interface
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
import sqlite3
from typing import List, Dict, Any

# Setup
ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
DB_PATH = ROOT / "data" / "timeout_bangkok_places.db"

app = FastAPI(title="Places Web Interface")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def index():
    """Main page - redirect to places"""
    return FileResponse(str(STATIC_DIR / "places.html"))

@app.get("/places")
def places_page():
    """Places page"""
    return FileResponse(str(STATIC_DIR / "places.html"))

@app.get("/api/places")
def api_places(city: str = "bangkok", flags: str = "", limit: int = 20):
    """
    Get places by city and flags.
    
    Args:
        city: City name (default: bangkok)
        flags: Comma-separated flags (e.g., "food_dining,art_exhibits")
        limit: Maximum number of places to return
    """
    try:
        if not DB_PATH.exists():
            raise HTTPException(status_code=500, detail="Database not found")
        
        # Connect to database
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        flag_list = [f.strip() for f in flags.split(",") if f.strip()] if flags else []
        
        if flag_list:
            # Get places by flags
            placeholders = ','.join(['?' for _ in flag_list])
            query = f"""
                SELECT DISTINCT p.* FROM places p
                JOIN places_fts fts ON p.id = fts.rowid
                WHERE p.city = ? AND (
                    fts.flags MATCH ? OR 
                    fts.tags MATCH ?
                )
                LIMIT ?
            """
            
            # For each flag, search in both flags and tags
            all_places = []
            for flag in flag_list:
                cursor.execute(query, (city, flag, flag, limit))
                places = cursor.fetchall()
                all_places.extend(places)
            
            # Remove duplicates and limit
            unique_places = []
            seen_ids = set()
            for place in all_places:
                if place[0] not in seen_ids and len(unique_places) < limit:
                    unique_places.append(place)
                    seen_ids.add(place[0])
            
            places = unique_places
        else:
            # Get all places
            cursor.execute("""
                SELECT * FROM places 
                WHERE city = ? 
                LIMIT ?
            """, (city, limit))
            places = cursor.fetchall()
        
        conn.close()
        
        # Convert to response format
        places_data = []
        for place in places:
            try:
                # Parse JSON fields
                tags = json.loads(place[9]) if place[9] else []
                flags = json.loads(place[10]) if place[10] else []
                photos = json.loads(place[17]) if place[17] else []
                
                place_dict = {
                    'id': place[0],
                    'name': place[1],
                    'city': place[2],
                    'domain': place[3],
                    'url': place[4],
                    'description': place[5],
                    'address': place[6],
                    'geo_lat': place[7],
                    'geo_lng': place[8],
                    'tags': tags,
                    'flags': flags,
                    'phone': place[11],
                    'email': place[12],
                    'website': place[13],
                    'hours': place[14],
                    'price_level': place[15],
                    'rating': place[16],
                    'photos': photos,
                    'image_url': place[18],
                    'quality_score': place[20]
                }
                places_data.append(place_dict)
            except Exception as e:
                print(f"Error parsing place {place[0]}: {e}")
                continue
        
        return {
            "city": city,
            "flags": flag_list,
            "places": places_data,
            "total": len(places_data)
        }
        
    except Exception as e:
        print(f"Error getting places: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get places: {str(e)}")

@app.get("/api/places/categories")
def api_places_categories():
    """Get available place categories/flags."""
    try:
        if not DB_PATH.exists():
            return {"categories": [], "description": "Database not found"}
        
        # Connect to database
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Get unique flags from places_fts
        cursor.execute("""
            SELECT DISTINCT value FROM places_fts 
            WHERE places_fts MATCH 'flags:*'
        """)
        
        flags = []
        for row in cursor.fetchall():
            try:
                # Parse flags from FTS
                flag_data = json.loads(row[0])
                if isinstance(flag_data, list):
                    flags.extend(flag_data)
            except:
                continue
        
        # Get unique tags too
        cursor.execute("""
            SELECT DISTINCT value FROM places_fts 
            WHERE places_fts MATCH 'tags:*'
        """)
        
        tags = []
        for row in cursor.fetchall():
            try:
                tag_data = json.loads(row[0])
                if isinstance(tag_data, list):
                    tags.extend(tag_data)
            except:
                continue
        
        conn.close()
        
        # Combine and deduplicate
        all_categories = list(set(flags + tags))
        all_categories.sort()
        
        return {
            "categories": all_categories,
            "description": "Available place categories for filtering"
        }
        
    except Exception as e:
        print(f"Error getting categories: {e}")
        return {"categories": [], "description": f"Error: {str(e)}"}

@app.get("/api/places/stats")
def api_places_stats(city: str = "bangkok"):
    """Get places statistics for a city."""
    try:
        if not DB_PATH.exists():
            return {"error": "Database not found"}
        
        # Connect to database
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Get total places
        cursor.execute("SELECT COUNT(*) FROM places WHERE city = ?", (city,))
        total_places = cursor.fetchone()[0]
        
        # Get places by quality
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN quality_score >= 0.7 THEN 1 ELSE 0 END) as high_quality,
                SUM(CASE WHEN quality_score < 0.7 THEN 1 ELSE 0 END) as low_quality
            FROM places 
            WHERE city = ?
        """, (city,))
        
        quality_stats = cursor.fetchone()
        
        # Get places by source
        cursor.execute("""
            SELECT source, COUNT(*) 
            FROM places 
            WHERE city = ? 
            GROUP BY source
        """, (city,))
        
        source_stats = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "city": city,
            "total_places": total_places,
            "quality_distribution": {
                "high_quality": quality_stats[1] or 0,
                "low_quality": quality_stats[2] or 0
            },
            "source_distribution": source_stats
        }
        
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Places Web Server...")
    print(f"📁 Static files: {STATIC_DIR}")
    print(f"🗄️  Database: {DB_PATH}")
    print(f"🌐 Server will be available at: http://localhost:8000")
    print(f"📍 Places page: http://localhost:8000/places")
    print(f"🔍 API: http://localhost:8000/api/places")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
