from dataclasses import dataclass
from typing import List, Literal
from datetime import date

@dataclass
class EventSource:
    name: str
    url: str
    type: Literal["website", "facebook", "api"]
    description: str
    free: bool

@dataclass
class Event:
    title: str
    date: str
    venue: str
    source: str
    url: str
    category: str
    description: str = ""
    event_date: date = None  # Для сортировки по датам

@dataclass
class DayEvents:
    date: str
    day_name: str
    events: List[Event]

@dataclass
class WeekEvents:
    days: List[DayEvents]
    total_events: int

@dataclass
class Category:
    id: str
    label: str
    tags: List[str]

@dataclass
class Place:
    id: str
    name: str
    city: str
    tags: List[str]
    typical_time: Literal["day", "evening"]
    source: str

@dataclass
class DayPlan:
    day: str
    activity: Place

@dataclass
class WeekPlan:
    days: List[DayPlan]
    total_activities: int

@dataclass
class PlanRequest:
    city: str
    selected_category_ids: List[str]

@dataclass
class PlanResponse:
    plan: str

@dataclass
class CategorySources:
    category_id: str
    sources: List[EventSource]

@dataclass
class SourcesResponse:
    categories: List[CategorySources]

@dataclass
class EventsResponse:
    events: List[Event]
    total: int
    category: str

@dataclass
class WeekEventsResponse:
    week_events: WeekEvents
    selected_categories: List[str]
