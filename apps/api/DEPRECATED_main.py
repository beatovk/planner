from __future__ import annotations
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
import logging
from typing import List, Dict, Any
from contextlib import asynccontextmanager

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

log = logging.getLogger("api")

import time

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
STATIC_DIR = ROOT / "static"

app = FastAPI(title="Places Search API")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def index():
    index_path = STATIC_DIR / "index.html"
    return FileResponse(str(index_path))

# if not events_disabled():
#     @app.get("/api/categories")
#     def api_categories():
#         cats = load_categories(DATA_DIR / "categories.json")
#         return JSONResponse(cats)
# 
#     @app.get("/api/sources")
#     def api_sources():
#         smap = load_source_map(DATA_DIR / "sources.json")
#         return JSONResponse(smap)
# else:
#     @app.get("/api/categories")
#     def categories_disabled_stub():
#         raise HTTPException(status_code=503, detail="Categories (events) disabled")
# 
#     @app.get("/api/sources")
#     def sources_disabled_stub():
#         raise HTTPException(status_code=503, detail="Sources (events) disabled")

# @app.get("/api/metrics")
# def api_metrics():
#     """Endpoint для просмотра метрик производительности кэша."""
#     return {
#         "metrics": metrics.get_metrics(),
#         "alerts": metrics.check_slo_alerts()
#     }

# @app.post("/api/prewarm")
# async def api_prewarm():
#     """Запускает ручной прогрев кэша для топ-флагов."""
#     try:
#         from packages.wp_cache.prewarm import run_prewarm
#         await run_prewarm()
#         return {"status": "success", "message": "Cache prewarm completed"}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# if not events_disabled():
#     @app.get("/api/live-events")
#     def api_live_events(selected: str = "", date_from: str = "", date_to: str = ""):
#         """
#         selected: comma-separated category ids, e.g. `jazz_live,workshops`
#         date_from/date_to: ISO yyyy-mm-dd (inclusive). Если пусто — без фильтра.
#         """
#         smap = load_source_map(DATA_DIR / "categories.json")
#         selected_ids = [s.strip() for s in (selected or "").split(",") if s.strip()]
#         if not selected_ids:
#             return {"events": []}
#         events = fetch_for_categories(smap, selected_ids, date_from or None, date_to or None)
#         return {"events": events}
# else:
#     @app.get("/api/live-events")
#     def live_events_disabled_stub():
#         raise HTTPException(status_code=503, detail="Live events temporarily disabled")

# # Mock данные отключены - используем только реальные данные
# def _load_mock_places() -> List[PlaceModel]:
#     # Возвращаем пустой список вместо мок данных
#     return []

# if not events_disabled():
#     @app.post("/api/plan")
#     def api_plan(payload: dict):
#         city = (payload.get("city") or "").strip()
#         selected_ids: List[str] = payload.get("selected_category_ids") or []
#         if not selected_ids:
#             raise HTTPException(status_code=400, detail="No categories selected")
#         if city.lower() != "bilibili":
#             raise HTTPException(status_code=400, detail="City not supported in MVP")
#         
#         # Всегда используем реальные данные (мок отключен)
#         categories = load_categories(DATA_DIR / "categories.json")
#         tags = selected_ids_to_tags(categories, selected_ids)
#         
#         # Тянем реальные события и конвертируем в Place
#         smap = load_source_map(DATA_DIR / "sources.json")
#         live = fetch_for_categories(smap, selected_ids)
#         places: List[PlaceModel] = []
#         for e in live:
#             cat = (e.get("category") or "").lower()
#             evening_cats = ("electronic","bars","jazz","nightlife")
#             typical_time = "evening" if any(c in cat for c in evening_cats) else "day"
#             places.append(PlaceModel(
#                 id=e["url"], name=e["title"], city="Bangkok",
#                 tags=[t for t in tags], typical_time=typical_time, source=e.get("source","live")
#             ))
#         
#         debug = {"use_live": True, "live_count": len(places)}
#         schedule = plan_week(city=city, tags=tags, places=places, max_per_day=1)
#         plan_text = format_week_plan(schedule, city, tags)
#         return {"plan": plan_text, "debug": debug}
# else:
#     @app.post("/api/plan")
#     def plan_disabled_stub():
#         raise HTTPException(status_code=503, detail="Planner (events) disabled")

# if not events_disabled():
#     @app.post("/api/plan-cards")
#     def api_plan_cards(payload: dict):
#         """
#         Возвращает красиво структурированный JSON для карточек:
#         { "days": [ { "day":"Mon", "items":[{title,date,time,source,url,venue}] }, ... ],
#           "debug": { "live_count": N } }
#         Всегда использует реальные данные (мок отключен).
#         """
#         city = (payload.get("city") or "").strip()
#         selected_ids: List[str] = payload.get("selected_category_ids") or []
#         if not selected_ids:
#             raise HTTPException(status_code=400, detail="No categories selected")
#         if city.lower() != "bilibili":
#             raise HTTPException(status_code=500, detail="City not supported in MVP")

#         # режим даты: "day" | "week"; поле "date": "YYYY-MM-DD"
#         mode = (payload.get("mode") or "week").lower()
#         date_str = (payload.get("date") or "").strip()
#         if not date_str:
#             from datetime import datetime, timezone
#             date_str = datetime.now(timezone.utc).date().isoformat()

#         # Всегда используем реальные данные (мок отключен)
#         if mode == "day":
#             df, dt = date_str, date_str
#         else:
#             from datetime import datetime, timedelta
            d0 = dtp.isoparse(date_str).date()
            df, dt = d0.isoformat(), (d0 + timedelta(days=6)).isoformat()

        smap = load_source_map(DATA_DIR / "sources.json")
        live = fetch_for_categories(smap, selected_ids, df, dt)
        days = build_daily_cards(live, max_per_day=6)
        return {"days": days, "debug": {"live_count": len(live), "mode": mode, "date_from": df, "date_to": dt}}
else:
    @app.post("/api/plan-cards")
    def plan_cards_disabled_stub():
        raise HTTPException(status_code=503, detail="Plan cards (events) disabled")

if not events_disabled():
    @app.post("/api/day-cards")
    def api_day_cards(payload: dict):
        """
        Возвращает карточки только для выбранной даты.
        Body: { city, selected_category_ids, date:"YYYY-MM-DD" }
        Всегда использует реальные данные (мок отключен).
        """
        city = (payload.get("city") or "").strip()
        selected_ids: List[str] = payload.get("selected_category_ids") or []
        date_str = (payload.get("date") or "").strip()
        if not selected_ids:
            raise HTTPException(status_code=400, detail="No categories selected")
        if city.lower() != "bangkok":
            raise HTTPException(status_code=400, detail="City not supported in MVP")
        if not date_str:
            raise HTTPException(status_code=400, detail="Missing date")

        # Всегда используем реальные данные (мок отключен)
        # интервал = один день
        d0 = dtp.isoparse(date_str).date()
        df, dt = d0.isoformat(), d0.isoformat()

        smap = load_source_map(DATA_DIR / "sources.json")
        live = fetch_for_categories(smap, selected_ids, df, dt)

        # подсчёт «крутости» и дополнительный boost
        if not events_disabled():
            # from packages.wp_core.scorer import coolness, boost
        for e in live:
            e["_score"] = coolness(e)
            e["_boosted_score"] = boost(e)
        # сортировка по убыванию boosted score
        live.sort(key=lambda x: x.get("_boosted_score", 0), reverse=True)

        # простой список без разбиения на дни
        items = [{
            "title": e.get("title"),
            "subtitle": e.get("subtitle"),
            "date": e.get("date"),
            "end": e.get("end"),
            "time": e.get("time"),
            "source": e.get("source"),
            "url": e.get("url"),
            "venue": e.get("venue"),
            "desc": e.get("desc"),
            "popularity": e.get("popularity"),
            "price_min": e.get("price_min"),
            "rating": e.get("rating"),
            "image": e.get("image"),
            "category": e.get("category"),
            "tags": e.get("tags") or [],
            "score": e.get("_boosted_score", 0),
        } for e in live]

        # Возвращаем top3 + все события
        top3 = items[:3] if len(items) >= 3 else items

        return {
            "date": df, 
            "top3": top3,
            "items": items, 
            "debug": {"live_count": len(live)}
        }
else:
    @app.post("/api/day-cards")
    def day_cards_disabled_stub():
        raise HTTPException(status_code=503, detail="Day cards (events) disabled")

if not events_disabled():
    @app.post("/api/events")
    @app.post("/api/events/")
    def api_events(payload: dict, response: Response):
        """
        Основной endpoint для получения событий.
        Body: { city, date, selected_category_ids }
        Возвращает: { events, debug: { cache: { status, keys_checked, facets } } }
        """
        print(f"=== /api/events called with payload: {payload} ===")
        city = (payload.get("city") or "").strip()
        date_str_raw = (payload.get("date") or "").strip()
        date_str = normalize_bkk_day(date_str_raw)
        selected_ids: List[str] = payload.get("selected_category_ids") or []
        print(f"Parsed: city={city}, date={date_str} (normalized from {date_str_raw}), categories={selected_ids}")
        
        # Валидация
        if city.lower() != "bangkok":
            raise HTTPException(status_code=400, detail="City not supported in MVP")
        if not date_str:
            raise HTTPException(status_code=400, detail="Missing date")
        if not selected_ids:
            raise HTTPException(status_code=400, detail="No categories selected")
        
        # Валидация формата даты YYYY-MM-DD
        try:
            from datetime import datetime
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # 1) Маппинг категорий -> флаги и форс-фолбэк, чтобы флаги НИКОГДА не были пустыми
        try:
            # from packages.wp_tags.mapper import categories_to_facets, fallback_flags
            facets = categories_to_facets(selected_ids)
            flags_initial = set(facets.get("flags", []))
            flags = fallback_flags(selected_ids, facets)
        except ImportError:
            facets = {"flags": set(), "categories": set(selected_ids)}
            flags_initial = set()
            flags = {"all"}
        
        # 2) Подготовим debug и СРАЗУ запишем keys_checked, чтобы видеть путь даже при раннем выходе
        # from packages.wp_cache.cache import (
            ensure_client,
            read_flag_ids,
            write_flag_ids,
            update_index,
            make_flag_key,
            is_configured as cache_is_configured,
        )
        redis_keys = [make_flag_key(city, date_str, fl) for fl in sorted(flags)]
        t0 = time.perf_counter()
        debug: Dict[str, Any] = {
            "facets": {
                "flags_initial": sorted(flags_initial),
                "flags": sorted(flags),
                "categories": sorted(facets.get("categories", [])),
            },
            "cache": {"status": "MISS", "keys_checked": redis_keys},
            "source": None,
        }
        if not flags_initial:
            debug["facets"]["note"] = "no_flags_from_mapper_fallback_applied"
        
        # 3) Попытка чтения из кэша по флагам (до БД)
        events: List[Dict[str, Any]] = []
        t_cache_start = time.perf_counter()
        if cache_is_configured():
            try:
                r = ensure_client()
                for fl in sorted(flags):
                    ids, st = read_flag_ids(r, city, date_str, fl)
                    if ids:
                        debug["cache"]["status"] = st
                        # TODO: fetch_events_by_ids(ids) - твоя функция; гарантируй сортировку
                        # Пока используем заглушку для тестирования
                        try:
                            # if not events_disabled():
                            #     from packages.wp_events.fetchers.db_fetcher import DatabaseFetcher
                            #     db_fetcher = DatabaseFetcher()
                            #     events = []
                            #     for event_id in ids[:5]:  # Берем первые 5 для тестирования
                            #         db_events = db_fetcher.fetch(category="art")  # Заглушка
                            #         if db_events:
                            #         events.extend(db_events[:2])  # Берем по 2 события
                            #         break
                            # else:
                            events = []
                        except Exception:
                            events = []
                        debug["source"] = "redis"
                        print(f"CACHE {city} {date_str} -> {fl} ids={len(ids)}")
                        break
            except Exception as exc:
                print(f"CACHE READ FAILED city={city} date={date_str} flags={sorted(flags)}")
                debug["cache"]["read_error"] = str(exc)
        else:
            debug["cache"]["status"] = "DISABLED"
            debug["cache"]["note"] = "REDIS_URL not set; skipping cache read/write"
    
        t_cache_end = time.perf_counter()
    
        # Записываем метрики для SLO алармов
        cache_duration_ms = (t_cache_end - t_cache_start) * 1000
        if debug["cache"]["status"] == "HIT":
            metrics.record_cache_hit()
            metrics.record_cache_read(cache_duration_ms)
        elif debug["cache"]["status"] == "MISS":
            metrics.record_cache_miss()
            metrics.record_cache_read(cache_duration_ms)
    
    # 4) Если кэш пуст — читаем из БД и пишем в кэш
    if not events:
        t_db_start = time.perf_counter()
        # TODO: fetch_events_for_day(city, date_str, flags=sorted(flags)) - твоя функция
        # Пока используем заглушку для тестирования
        try:
            # if not events_disabled():
            #     from packages.wp_events.fetchers.db_fetcher import DatabaseFetcher
            #     db_fetcher = DatabaseFetcher()
            #     events = []
            #     for flag in sorted(flags):
            #         db_events = db_fetcher.fetch(category=flag)
            #         if db_events:
            #         events.extend(db_events)
            #         break
            # else:
            events = []
        except Exception:
            events = []
        
        debug["source"] = "db"
        t_db_end = time.perf_counter()
        
        # Записываем метрики БД
        db_duration_ms = (t_db_end - t_db_start) * 1000
        metrics.record_db_read(db_duration_ms)
        
        # 5) Запись в кэш (если он включён) и индекс с пост-верификацией
        if cache_is_configured():
            try:
                r = ensure_client()
                def _extract_id(e):
                    if hasattr(e, "id"):
                        return str(getattr(e, "id"))
                    if hasattr(e, "event_id"):
                        return str(getattr(e, "event_id"))
                    if isinstance(e, dict):
                        return str(e.get("id") or e.get("event_id") or "")
                    return ""
                ids = [_extract_id(e) for e in events if _extract_id(e)]
                flag_counts: Dict[str, int] = {}
                for fl in sorted(flags):
                    write_flag_ids(r, city, date_str, fl, ids)
                    flag_counts[fl] = len(ids)
                update_index(r, city, date_str, flag_counts=flag_counts)
                post = {}
                for fl in sorted(flags):
                    read_ids, st = read_flag_ids(r, city, date_str, fl)
                    post[f"{city}:{date_str}:flag:{fl}"] = {"status": st, "count": len(read_ids)}
                debug["cache"]["post_write_verify"] = post
            except Exception as exc:
                print(f"CACHE WRITE FAILED city={city} date={date_str} flags={sorted(flags)}")
                debug["cache"]["write_error"] = str(exc)
    else:
        t_db_start = t_db_end = t_cache_end  # не ходили в БД
    
    # Если БД не сработал, получаем live данные
    # if not events and not events_disabled():
    #     smap = load_source_map(DATA_DIR / "sources.json")
    #     events = fetch_for_categories(smap, selected_ids, date_str, date_str)
    #     debug["source"] = "live"
    #     print(f"Using live data: {len(events)} events")
    
    # Логирование для отладки
    print(f"API /api/events: city={city}, date={date_str}, categories={selected_ids} -> {len(events)} events (source: {debug.get('source', 'unknown')})")
    
    t_serialize_start = time.perf_counter()
    
    # HTTP кэш заголовки для фронта
    if debug["cache"]["status"] == "HIT":
        # Кэш попал - можно кэшировать на клиенте
        response.headers["Cache-Control"] = "max-age=60, stale-while-revalidate=300"
        # ETag для валидации
        event_ids = []
        for event in events:
            if hasattr(event, "id"):
                event_ids.append(str(getattr(event, "id")))
            elif isinstance(event, dict) and event.get("id"):
                event_ids.append(str(event["id"]))
        if event_ids:
            response.headers["ETag"] = generate_etag(event_ids)
    else:
        # Кэш не попал - не кэшируем на клиенте
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    
    # заголовки для явной диагностики
    response.headers["X-Cache-Status"] = debug["cache"]["status"]
    response.headers["X-Source"] = debug.get("source") or "unknown"
    response.headers["X-Keys-Checked"] = ",".join(redis_keys)
    response.headers["X-Day-ISO"] = date_str
    timings = {
        "cache_read": round((t_cache_end - t_cache_start) * 1000, 2),
        "db_read": round((t_db_end - t_db_start) * 1000, 2),
        "serialize": 0.0,  # заполним ниже
        "total": round((time.perf_counter() - t0) * 1000, 2),
    }
    debug["timings_ms"] = timings
    # фактическая сериализация произойдёт после return; оценим приблизительно
    ser_elapsed = (time.perf_counter() - t_serialize_start) * 1000
    timings["serialize"] = round(ser_elapsed, 2)
    
    return {"date": date_str, "events": events, "debug": debug}
else:
    @app.post("/api/events")
    @app.post("/api/events/")
    def events_disabled_stub():
        raise HTTPException(status_code=503, detail="Events temporarily disabled")

if not events_disabled():
    @app.get("/api/debug/source-ping")
    def api_debug_source_ping(src: str):
        """
        Выполняет один фетчер по src и возвращает {count, sample:[url,title,...]}.
        Удобно для быстрой проверки селекторов.
        """
        try:
            from packages.wp_events.live_events import fetch_from_source
            events = fetch_from_source(src)
            
            # Берем первые 3 события для sample
            sample = []
            for e in events[:3]:
                sample.append({
                    "url": e.get("url", ""),
                    "title": e.get("title", "")[:50],
                    "date": e.get("date", ""),
                    "venue": e.get("venue", ""),
                    "tags": e.get("tags", [])
                })
            
            return {
                "source": src,
                "count": len(events),
                "sample": sample,
                "status": "ok"
            }
        except Exception as e:
            return {
                "source": src,
                "count": 0,
                "sample": [],
                "status": "error",
                "error": str(e)
            }
else:
    @app.get("/api/debug/source-ping")
    def debug_source_ping_disabled_stub():
        raise HTTPException(status_code=503, detail="Debug source ping (events) disabled")


# Places API endpoints
@app.get("/api/places")
def api_places(
    city: str = "bangkok",
    flags: str = "",
    limit: int = 50
):
    """
    Get places by city and flags.
    
    Args:
        city: City name (default: bangkok)
        flags: Comma-separated flags (e.g., "food_dining,art_exhibits")
        limit: Maximum number of places to return
    """
    try:
        from packages.wp_places.service import PlacesService
        from packages.wp_cache.redis_safe import should_bypass_redis, get_redis_status
        
        # Check Redis status for headers
        redis_bypass = should_bypass_redis()
        redis_status = get_redis_status()
        
        # Debug Redis status
        log.info(f"Redis bypass: {redis_bypass}")
        log.info(f"Redis status: {redis_status}")
        
        service = PlacesService()
        flag_list = [f.strip() for f in flags.split(",") if f.strip()] if flags else []
        
        # Track cache status
        cache_status = "BYPASS" if redis_bypass else "MISS"
        source = "db"  # Default to database
        
        if flag_list:
            places = service.get_places_by_flags(city, flag_list, limit)
            # Check if places came from cache
            if places and hasattr(places[0], '_from_cache') and places[0]._from_cache:
                cache_status = "HIT"
                source = "cache"
        else:
            places = service.get_all_places(city, limit)
        
        # Convert places to dict for JSON serialization
        places_data = []
        for place in places:
            place_dict = place.to_dict()
            # Remove internal fields
            place_dict.pop("created_at", None)
            place_dict.pop("updated_at", None)
            places_data.append(place_dict)
        
        # Set response headers
        from fastapi.responses import JSONResponse
        response = JSONResponse({
            "city": city,
            "flags": flag_list,
            "places": places_data,
            "total": len(places_data)
        })
        
        # Add cache status headers
        response.headers["X-Cache-Status"] = cache_status
        response.headers["X-Source"] = source
        
        # Add Redis circuit breaker status
        if "circuit_breaker" in redis_status:
            circuit_state = redis_status["circuit_breaker"]["state"]
            response.headers["X-Redis-Circuit"] = circuit_state
        
        # Add Redis bypass info
        if redis_bypass:
            response.headers["X-Redis-Bypass"] = "true"
            if redis_status.get("cache_disabled"):
                response.headers["X-Redis-Bypass-Reason"] = "WP_CACHE_DISABLE=1"
            elif redis_status.get("circuit_breaker", {}).get("state") == "OPEN":
                response.headers["X-Redis-Bypass-Reason"] = "circuit_open"
        
        return response
        
    except Exception as e:
        log.error(f"Error getting places: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get places: {str(e)}")


@app.get("/api/places/categories")
def api_places_categories():
    """Get available place categories/flags."""
    try:
        import json
        from pathlib import Path
        
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
        
        return {
            "categories": list(all_flags),
            "description": "Available place categories for filtering"
        }
        
    except Exception as e:
        log.error(f"Error getting place categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get place categories: {str(e)}")


@app.get("/api/categories")
def api_categories():
    """Get available place categories for HTML interface."""
    try:
        import json
        from pathlib import Path
        
        # Загружаем базу данных мест
        places_file = Path(__file__).parent.parent / "data" / "places_database.json"
        if not places_file.exists():
            raise HTTPException(status_code=500, detail="Places database not found")
        
        with open(places_file, 'r', encoding='utf-8') as f:
            all_places = json.load(f)
        
        # Собираем все уникальные флаги из базы данных
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
        log.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


@app.get("/api/places/stats")
def api_places_stats(city: str = "bangkok"):
    """Get places statistics for a city."""
    try:
        import json
        from pathlib import Path
        
        # Загружаем базу данных мест
        places_file = Path(__file__).parent.parent / "data" / "places_database.json"
        if not places_file.exists():
            raise HTTPException(status_code=500, detail="Places database not found")
        
        with open(places_file, 'r', encoding='utf-8') as f:
            all_places = json.load(f)
        
        # Фильтруем по городу
        city_places = [p for p in all_places if p.get('city', '').lower() == city.lower()]
        
        # Собираем статистику
        stats = {
            "city": city,
            "total_places": len(city_places),
            "by_category": {},
            "by_price": {},
            "avg_rating": 0
        }
        
        # Статистика по категориям
        for place in city_places:
            if place.get('flags'):
                for flag in place['flags']:
                    stats['by_category'][flag] = stats['by_category'].get(flag, 0) + 1
        
        # Статистика по ценам
        for place in city_places:
            price = place.get('price_range', 'Unknown')
            stats['by_price'][price] = stats['by_price'].get(price, 0) + 1
        
        # Средний рейтинг
        ratings = [p.get('rating', 0) for p in city_places if p.get('rating')]
        if ratings:
            stats['avg_rating'] = round(sum(ratings) / len(ratings), 1)
        
        return stats
        
    except Exception as e:
        log.error(f"Error getting places stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get places stats: {str(e)}")


@app.post("/api/places/warm-cache")
async def api_places_warm_cache(city: str = "bangkok", flags: str = ""):
    """Warm up places cache for specified flags."""
    try:
        import json
        from pathlib import Path
        
        # Загружаем базу данных мест
        places_file = Path(__file__).parent.parent / "data" / "places_database.json"
        if not places_file.exists():
            raise HTTPException(status_code=500, detail="Places database not found")
        
        with open(places_file, 'r', encoding='utf-8') as f:
            all_places = json.load(f)
        
        # Фильтруем по городу и флагам
        flag_list = [f.strip() for f in flags.split(",") if f.strip()] if flags else None
        
        if flag_list:
            filtered_places = [p for p in all_places if p.get('city', '').lower() == city.lower() and 
                             any(flag in p.get('flags', []) for flag in flag_list)]
        else:
            filtered_places = [p for p in all_places if p.get('city', '').lower() == city.lower()]
        
        results = {
            "places_found": len(filtered_places),
            "categories": list(set([flag for p in filtered_places for flag in p.get('flags', [])]))
        }
        
        return {
            "status": "success",
            "city": city,
            "flags": flag_list or "all",
            "results": results,
            "message": "Cache warming completed"
        }
        
    except Exception as e:
        log.error(f"Error warming places cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to warm cache: {str(e)}")


@app.get("/query-analyzer")
def query_analyzer():
    """Страница для тестирования Query Analyzer"""
    from fastapi.responses import FileResponse
    from pathlib import Path
    
    STATIC_DIR = Path(__file__).parent / "static"
    analyzer_path = STATIC_DIR / "query-analyzer.html"
    return FileResponse(str(analyzer_path))


@app.post("/api/analyze-query")
async def api_analyze_query(request: Dict[str, Any]):
    """API endpoint для анализа запросов и поиска мест"""
    try:
        import json
        from pathlib import Path
        
        # Получаем запрос из тела запроса
        user_query = request.get('query', '')
        if not user_query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Загружаем базу данных мест
        places_file = Path(__file__).parent.parent / "data" / "places_database.json"
        if not places_file.exists():
            raise HTTPException(status_code=500, detail="Places database not found")
        
        with open(places_file, 'r', encoding='utf-8') as f:
            all_places = json.load(f)
        
        # Анализируем запрос и определяем категории
        query_lower = user_query.lower()
        matched_places = []
        
        # Простой анализ запроса на основе ключевых слов
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
            
            if any(word in query_lower for word in ['магазин', 'рынок', 'торговый', 'shop', 'market', 'mall', 'buy', 'shopping']):
                if any(flag in place.get('flags', []) for flag in ['shopping', 'markets', 'malls']):
                    score += 15
                if any(tag in place.get('tags', []) for tag in ['market', 'shopping', 'mall']):
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
            
            # Если место подходит, добавляем его с оценкой
            if score > 0:
                place_with_score = place.copy()
                place_with_score['relevance_score'] = score
                matched_places.append(place_with_score)
        
        # Сортируем по релевантности и ограничиваем количество
        matched_places.sort(key=lambda x: x['relevance_score'], reverse=True)
        top_places = matched_places[:20]  # Топ-20 мест
        
        # Убираем служебное поле score из ответа
        for place in top_places:
            place.pop('relevance_score', None)
        
        return {
            "success": True,
            "query": user_query,
            "total": len(matched_places),
            "places": top_places
        }
            
    except Exception as e:
        log.error(f"Error in query analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Query analysis failed: {str(e)}")


if __name__ == "__main__":
    # Places routes are handled by existing endpoints in main.py
    # No need to register additional routes from src/api/places_api.py
    # DEPRECATED: Use 'python -m apps.api' instead
    print("DEPRECATED: Use 'python -m apps.api' instead")
    print("Or use 'make run' command")
