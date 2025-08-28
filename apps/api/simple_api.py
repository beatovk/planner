from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
from typing import Dict, Any

app = FastAPI(title="Places Search API")

# Настраиваем статические файлы
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static"

@app.get("/")
def index():
    """Главная страница"""
    index_path = STATIC_DIR / "index.html"
    return FileResponse(str(index_path))

@app.get("/query-analyzer")
def query_analyzer():
    """Страница для поиска мест"""
    analyzer_path = STATIC_DIR / "query-analyzer.html"
    return FileResponse(str(analyzer_path))

@app.get("/api/categories")
def api_categories():
    """Получить доступные категории мест"""
    try:
        # Загружаем базу данных мест
        places_file = Path(__file__).parent.parent / "data" / "places_database.json"
        if not places_file.exists():
            raise HTTPException(status_code=500, detail="Places database not found")
        
        with open(places_file, 'r', encoding='utf-8') as f:
            all_places = json.load(f)
        
        # Собираем все уникальные флаги
        all_flags = set()
        for place in all_places:
            if place.get('flags'):
                all_flags.update(place['flags'])
        
        # Преобразуем в формат для HTML
        categories_data = []
        for flag in sorted(all_flags):
            categories_data.append({
                "id": flag,
                "label": flag.replace("_", " ").title(),
                "tags": [flag]
            })
        
        return categories_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@app.post("/api/analyze-query")
async def api_analyze_query(request: Dict[str, Any]):
    """Поиск мест по запросу"""
    try:
        # Получаем запрос
        user_query = request.get('query', '')
        if not user_query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Загружаем базу данных мест
        places_file = Path(__file__).parent.parent / "data" / "places_database.json"
        if not places_file.exists():
            raise HTTPException(status_code=500, detail="Places database not found")
        
        with open(places_file, 'r', encoding='utf-8') as f:
            all_places = json.load(f)
        
        # Простой поиск по ключевым словам
        query_lower = user_query.lower()
        matched_places = []
        
        for place in all_places:
            score = 0
            
            # Проверяем название
            if any(word in place['name'].lower() for word in query_lower.split()):
                score += 10
            
            # Проверяем описание
            if place.get('description'):
                if any(word in place['description'].lower() for word in query_lower.split()):
                    score += 5
            
            # Проверяем теги
            if place.get('tags'):
                for tag in place['tags']:
                    if any(word in tag.lower() for word in query_lower.split()):
                        score += 8
            
            # Проверяем флаги
            if place.get('flags'):
                for flag in place['flags']:
                    if any(word in flag.lower() for word in query_lower.split()):
                        score += 6
            
            # Специальные правила для категорий
            if any(word in query_lower for word in ['еда', 'есть', 'ресторан', 'кафе', 'кухня', 'food', 'eat', 'restaurant', 'cafe', 'dining']):
                if any(flag in place.get('flags', []) for flag in ['food_dining', 'thai_cuisine', 'cafes']):
                    score += 15
                if any(tag in place.get('tags', []) for tag in ['food', 'restaurant', 'cafe']):
                    score += 10
            
            if any(word in query_lower for word in ['парк', 'природа', 'прогулка', 'park', 'nature', 'outdoor', 'walk']):
                if any(flag in place.get('flags', []) for flag in ['parks', 'nature']):
                    score += 15
                if any(tag in place.get('tags', []) for tag in ['park', 'nature']):
                    score += 10
            
            if any(word in query_lower for word in ['искусство', 'музей', 'галерея', 'art', 'museum', 'gallery', 'exhibition']):
                if any(flag in place.get('flags', []) for flag in ['art_exhibits', 'culture']):
                    score += 15
                if any(tag in place.get('tags', []) for tag in ['art', 'museum', 'gallery']):
                    score += 10
            
            if any(word in query_lower for word in ['развлечения', 'музыка', 'клуб', 'entertainment', 'music', 'club', 'jazz', 'electronic']):
                if any(flag in place.get('flags', []) for flag in ['entertainment', 'jazz', 'electronic']):
                    score += 15
                if any(tag in place.get('tags', []) for tag in ['jazz', 'live music', 'electronic', 'club']):
                    score += 10
            
            if any(word in query_lower for word in ['спа', 'массаж', 'йога', 'wellness', 'spa', 'massage', 'yoga']):
                if any(flag in place.get('flags', []) for flag in ['wellness', 'traditional', 'fitness']):
                    score += 15
                if any(tag in place.get('tags', []) for tag in ['wellness', 'spa', 'massage', 'yoga']):
                    score += 10
            
            if any(word in query_lower for word in ['крыша', 'вид', 'rooftop', 'view', 'sky']):
                if any(flag in place.get('flags', []) for flag in ['rooftop']):
                    score += 15
                if any(tag in place.get('tags', []) for tag in ['rooftop', 'view']):
                    score += 10
            
            # Если место подходит, добавляем его
            if score > 0:
                place_with_score = place.copy()
                place_with_score['relevance_score'] = score
                matched_places.append(place_with_score)
        
        # Сортируем по релевантности
        matched_places.sort(key=lambda x: x['relevance_score'], reverse=True)
        top_places = matched_places[:20]  # Топ-20 мест
        
        # Убираем служебное поле score
        for place in top_places:
            place.pop('relevance_score', None)
        
        return {
            "success": True,
            "query": user_query,
            "total": len(matched_places),
            "places": top_places
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query analysis failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
