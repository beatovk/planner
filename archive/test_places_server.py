#!/usr/bin/env python
"""
Simple test server for places API.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import sys
from pathlib import Path

# Добавляем корневую директорию в Python path
sys.path.insert(0, str(Path(__file__).parent))

app = FastAPI(title="Places Test Server")

# Mount static files
from pathlib import Path
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def index():
    return {"message": "Places Test Server", "status": "running"}

@app.get("/places")
def places_page():
    """Serve the places HTML page."""
    from pathlib import Path
    places_html = Path(__file__).parent / "static" / "places.html"
    if places_html.exists():
        return FileResponse(str(places_html))
    else:
        return {"error": "Places HTML file not found"}

@app.get("/api/places/categories")
def api_places_categories():
    """Get available place categories/flags."""
    # Возвращаем статические данные для тестирования
    categories = [
        "electronic_music",
        "live_music", 
        "jazz_blues",
        "rooftop",
        "food_dining",
        "art_exhibits",
        "workshops",
        "cinema",
        "markets",
        "yoga_wellness",
        "parks"
    ]
    
    return {
        "categories": categories,
        "description": "Available place categories for filtering"
    }

@app.get("/api/places")
def api_places(city: str = "bangkok", flags: str = "", limit: int = 20):
    """
    Get places by city and flags.
    """
    # Возвращаем тестовые данные
    flag_list = [f.strip() for f in flags.split(",") if f.strip()] if flags else []
    
    # Создаем тестовые места
    test_places = [
            {
                "id": "test1",
                "name": "Thai Delight Restaurant",
                "description": "Authentic Thai cuisine in Sukhumvit",
                "flags": ["food_dining"],
                "area": "Sukhumvit",
                "price_level": 2,
                "source": "test"
            },
            {
                "id": "test2", 
                "name": "Bangkok Art Space",
                "description": "Contemporary art gallery in Silom",
                "flags": ["art_exhibits"],
                "area": "Silom",
                "price_level": 1,
                "source": "test"
            },
            {
                "id": "test3",
                "name": "Electric Beats Club",
                "description": "Electronic music venue in Thonglor",
                "flags": ["electronic_music"],
                "area": "Thonglor", 
                "price_level": 3,
                "source": "test"
            },
            {
                "id": "test4",
                "name": "Rooftop Skybar",
                "description": "Luxury rooftop bar with city views",
                "flags": ["rooftop", "food_dining"],
                "area": "Sukhumvit",
                "price_level": 4,
                "source": "test"
            },
            {
                "id": "test5",
                "name": "Chatuchak Market",
                "description": "World's largest weekend market",
                "flags": ["markets"],
                "area": "Chatuchak",
                "price_level": 1,
                "source": "test"
            },
            {
                "id": "test6",
                "name": "Lumpini Park",
                "description": "Beautiful green oasis in the heart of Bangkok",
                "flags": ["parks"],
                "area": "Silom",
                "price_level": 0,
                "source": "test"
            },
            {
                "id": "test7",
                "name": "Bangkok Film Archive",
                "description": "Cinema museum and screening room",
                "flags": ["cinema", "art_exhibits"],
                "area": "Thonburi",
                "price_level": 1,
                "source": "test"
            },
            {
                "id": "test8",
                "name": "Yoga Studio Sukhumvit",
                "description": "Peaceful yoga and meditation center",
                "flags": ["yoga_wellness"],
                "area": "Sukhumvit",
                "price_level": 2,
                "source": "test"
            }
        ]
    
    # Фильтруем по флагам если указаны
    if flag_list:
        filtered_places = [
            place for place in test_places 
            if any(flag in place["flags"] for flag in flag_list)
        ]
    else:
        filtered_places = test_places
    
    # Применяем лимит
    if limit:
        filtered_places = filtered_places[:limit]
    
    return {
        "city": city,
        "flags": flag_list,
        "places": filtered_places,
        "total": len(filtered_places)
    }

@app.get("/api/places/stats")
def api_places_stats(city: str = "bangkok"):
    """Get places statistics for a city."""
    return {
        "city": city,
        "total_places": 3,
        "by_flags": {
            "food_dining": 1,
            "art_exhibits": 1,
            "electronic_music": 1
        },
        "by_sources": {
            "test": 3
        }
    }

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "places"}

if __name__ == "__main__":
    print("🚀 Starting Places Test Server on http://localhost:8001")
    print("📖 API Documentation: http://localhost:8001/docs")
    print("🔍 Health check: http://localhost:8001/health")
    print("🏪 Places API: http://localhost:8001/api/places")
    print("📊 Stats API: http://localhost:8001/api/places/stats")
    print("🏷️ Categories API: http://localhost:8001/api/places/categories")
    print("\nPress Ctrl+C to stop the server")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
