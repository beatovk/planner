"""
Places API routes registration.

This module provides the register_places_routes function to register
all places-related endpoints with a FastAPI application.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

# Создаем роутер для мест
places_router = APIRouter(prefix="/api/places", tags=["places"])


@places_router.get("/health")
async def health_check():
    """Проверка здоровья API мест"""
    return {"status": "healthy", "service": "places-api", "version": "1.0.0"}


@places_router.get("/search")
async def search_places(
    query: str, city: Optional[str] = "bangkok", limit: Optional[int] = 20
):
    """Поиск мест по запросу"""
    try:
        # Загружаем базу данных мест
        places_file = (
            Path(__file__).parent.parent.parent / "data" / "places_database.json"
        )
        if not places_file.exists():
            raise HTTPException(status_code=500, detail="Places database not found")

        with open(places_file, "r", encoding="utf-8") as f:
            all_places = json.load(f)

        # Фильтруем по городу
        city_places = [
            p for p in all_places if p.get("city", "").lower() == city.lower()
        ]

        # Простой поиск по ключевым словам
        query_lower = query.lower()
        matched_places = []

        for place in city_places:
            score = 0

            # Проверяем название
            if any(word in place["name"].lower() for word in query_lower.split()):
                score += 10

            # Проверяем описание
            if place.get("description"):
                if any(
                    word in place["description"].lower() for word in query_lower.split()
                ):
                    score += 5

            # Проверяем теги
            if place.get("tags"):
                for tag in place["tags"]:
                    if any(word in tag.lower() for word in query_lower.split()):
                        score += 8

            # Проверяем флаги
            if place.get("flags"):
                for flag in place["flags"]:
                    if any(word in flag.lower() for word in query_lower.split()):
                        score += 6

            # Специальные правила для категорий
            if any(
                word in query_lower
                for word in [
                    "еда",
                    "есть",
                    "ресторан",
                    "кафе",
                    "кухня",
                    "food",
                    "eat",
                    "restaurant",
                    "cafe",
                    "dining",
                ]
            ):
                if any(
                    flag in place.get("flags", [])
                    for flag in ["food_dining", "thai_cuisine", "cafes"]
                ):
                    score += 15
                if any(
                    tag in place.get("tags", [])
                    for tag in ["food", "restaurant", "cafe"]
                ):
                    score += 10

            if any(
                word in query_lower
                for word in [
                    "парк",
                    "природа",
                    "прогулка",
                    "park",
                    "nature",
                    "outdoor",
                    "walk",
                ]
            ):
                if any(flag in place.get("flags", []) for flag in ["parks", "nature"]):
                    score += 15
                if any(tag in place.get("tags", []) for tag in ["park", "nature"]):
                    score += 10

            if any(
                word in query_lower
                for word in [
                    "искусство",
                    "музей",
                    "галерея",
                    "art",
                    "museum",
                    "gallery",
                    "exhibition",
                ]
            ):
                if any(
                    flag in place.get("flags", [])
                    for flag in ["art_exhibits", "culture"]
                ):
                    score += 15
                if any(
                    tag in place.get("tags", []) for tag in ["art", "museum", "gallery"]
                ):
                    score += 10

            if any(
                word in query_lower
                for word in [
                    "развлечения",
                    "музыка",
                    "клуб",
                    "entertainment",
                    "music",
                    "club",
                    "jazz",
                    "electronic",
                ]
            ):
                if any(
                    flag in place.get("flags", [])
                    for flag in ["entertainment", "jazz", "electronic"]
                ):
                    score += 15
                if any(
                    tag in place.get("tags", [])
                    for tag in ["jazz", "live music", "electronic", "club"]
                ):
                    score += 10

            if any(
                word in query_lower
                for word in [
                    "спа",
                    "массаж",
                    "йога",
                    "wellness",
                    "spa",
                    "massage",
                    "yoga",
                ]
            ):
                if any(
                    flag in place.get("flags", [])
                    for flag in ["wellness", "traditional", "fitness"]
                ):
                    score += 15
                if any(
                    tag in place.get("tags", [])
                    for tag in ["wellness", "spa", "massage", "yoga"]
                ):
                    score += 10

            if any(
                word in query_lower
                for word in ["крыша", "вид", "rooftop", "view", "sky"]
            ):
                if any(flag in place.get("flags", []) for flag in ["rooftop"]):
                    score += 15
                if any(tag in place.get("tags", []) for tag in ["rooftop", "view"]):
                    score += 10

            # Если место подходит, добавляем его
            if score > 0:
                place_with_score = place.copy()
                place_with_score["relevance_score"] = score
                matched_places.append(place_with_score)

        # Сортируем по релевантности и ограничиваем количество
        matched_places.sort(key=lambda x: x["relevance_score"], reverse=True)
        top_places = matched_places[:limit]

        # Убираем служебное поле score
        for place in top_places:
            place.pop("relevance_score", None)

        return {
            "success": True,
            "query": query,
            "city": city,
            "total": len(matched_places),
            "places": top_places,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@places_router.get("/recommend")
async def recommend_places(
    city: Optional[str] = "bangkok",
    category: Optional[str] = None,
    limit: Optional[int] = 10,
):
    """Рекомендации мест по категории"""
    try:
        # Загружаем базу данных мест
        places_file = (
            Path(__file__).parent.parent.parent / "data" / "places_database.json"
        )
        if not places_file.exists():
            raise HTTPException(status_code=500, detail="Places database not found")

        with open(places_file, "r", encoding="utf-8") as f:
            all_places = json.load(f)

        # Фильтруем по городу
        city_places = [
            p for p in all_places if p.get("city", "").lower() == city.lower()
        ]

        # Фильтруем по категории если указана
        if category:
            filtered_places = []
            for place in city_places:
                if (
                    place.get("flags")
                    and category.lower() in [f.lower() for f in place["flags"]]
                ) or (
                    place.get("tags")
                    and category.lower() in [t.lower() for t in place["tags"]]
                ):
                    filtered_places.append(place)
            city_places = filtered_places

        # Сортируем по рейтингу и ограничиваем количество
        sorted_places = sorted(
            city_places, key=lambda x: x.get("rating", 0), reverse=True
        )
        recommended_places = sorted_places[:limit]

        return {
            "success": True,
            "city": city,
            "category": category,
            "total": len(city_places),
            "places": recommended_places,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")
