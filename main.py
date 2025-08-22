from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
import json
import os
from core.planner import WeekPlanner
from core.types import Category, Place, PlanRequest, PlanResponse, EventSource, CategorySources, SourcesResponse, Event, EventsResponse, WeekEventsResponse, WeekEvents, DayEvents
from core.scraper import EventScraper
from datetime import date, timedelta

app = FastAPI(title="Bangkok Week Planner")

# Подключаем статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Загружаем данные
def load_data():
    with open("data/categories.json", "r", encoding="utf-8") as f:
        categories = [Category(**cat) for cat in json.load(f)]
    
    with open("data/mock_places.json", "r", encoding="utf-8") as f:
        places = [Place(**place) for place in json.load(f)]
    
    return categories, places

# Загружаем источники
def load_sources():
    with open("data/sources.json", "r", encoding="utf-8") as f:
        return json.load(f)

categories, places = load_data()
sources = load_sources()
planner = WeekPlanner(categories, places)
scraper = EventScraper()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/categories")
async def get_categories():
    return categories

@app.get("/api/sources")
async def get_sources():
    """Получить источники событий для всех категорий"""
    category_sources = []
    
    for category in categories:
        if category.id in sources:
            source_list = [EventSource(**source) for source in sources[category.id]["sources"]]
            category_sources.append(CategorySources(
                category_id=category.id,
                sources=source_list
            ))
    
    return SourcesResponse(categories=category_sources)

@app.get("/api/sources/{category_id}")
async def get_category_sources(category_id: str):
    """Получить источники событий для конкретной категории"""
    if category_id not in sources:
        raise HTTPException(status_code=404, detail="Category not found")
    
    source_list = [EventSource(**source) for source in sources[category_id]["sources"]]
    return CategorySources(category_id=category_id, sources=source_list)

@app.get("/api/events/{category_id}")
async def get_category_events(category_id: str):
    """Получить реальные события для конкретной категории из всех источников"""
    if category_id not in [cat.id for cat in categories]:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Используем scraper для получения событий
    events_data = scraper.scrape_all_sources(category_id)
    
    # Конвертируем в объекты Event
    events = [Event(**event) for event in events_data]
    
    return EventsResponse(
        events=events,
        total=len(events),
        category=category_id
    )

@app.get("/api/events")
async def get_all_events():
    """Получить события для всех категорий"""
    all_events = []
    
    for category in categories:
        events_data = scraper.scrape_all_sources(category.id)
        # events_data уже содержит объекты Event, не нужно их конвертировать
        all_events.extend(events_data)
    
    return EventsResponse(
        events=all_events,
        total=len(all_events),
        category="all"
    )

@app.post("/api/week-plan")
async def create_week_plan(request: PlanRequest):
    """Создать план событий на неделю для выбранных категорий"""
    if request.city != "Bangkok":
        raise HTTPException(status_code=400, detail="City not supported in MVP")
    
    if not request.selected_category_ids:
        raise HTTPException(status_code=400, detail="At least one category must be selected")
    
    # Получаем события для выбранных категорий
    all_events = scraper.get_week_events_by_categories(request.selected_category_ids)
    
    # Группируем события по дням
    week_dates = scraper.get_week_dates()
    days_events = []
    
    for day_info in week_dates:
        # Находим события для этого дня
        day_events = [event for event in all_events if event.event_date == day_info['date_obj']]
        
        if day_events:  # Показываем только дни с событиями
            days_events.append(DayEvents(
                date=day_info['date'],
                day_name=day_info['day_name'],
                events=day_events
            ))
    
    week_events = WeekEvents(
        days=days_events,
        total_events=len(all_events)
    )
    
    return WeekEventsResponse(
        week_events=week_events,
        selected_categories=request.selected_category_ids
    )

@app.post("/api/plan")
async def create_plan(request: PlanRequest):
    """Старый API для совместимости - теперь возвращает пустой план"""
    if request.city != "Bangkok":
        raise HTTPException(status_code=400, detail="City not supported in MVP")
    
    if not request.selected_category_ids:
        raise HTTPException(status_code=400, detail="At least one category must be selected")
    
    # Возвращаем пустой план, так как теперь используем новый API
    return PlanResponse(plan="")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
