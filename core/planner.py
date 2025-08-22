import json
from typing import List, Dict
from .types import Category, Place, DayPlan, WeekPlan

class WeekPlanner:
    def __init__(self, categories: List[Category], places: List[Place]):
        self.categories = categories
        self.places = places
        self.category_map = {cat.id: cat for cat in categories}
    
    def get_selected_tags(self, category_ids: List[str]) -> List[str]:
        """Получает все теги из выбранных категорий"""
        tags = []
        for cat_id in category_ids:
            if cat_id in self.category_map:
                tags.extend(self.category_map[cat_id].tags)
        return list(set(tags))  # Убираем дубликаты
    
    def score_places(self, places: List[Place], target_tags: List[str]) -> List[Place]:
        """Скорит места по релевантности тегам"""
        if not target_tags:
            return sorted(places, key=lambda x: x.name)
        
        scored_places = []
        for place in places:
            score = 0
            place_tags = [tag.lower() for tag in place.tags]
            
            # Считаем совпадающие теги
            for tag in target_tags:
                if tag.lower() in place_tags:
                    score += 1
            
            scored_places.append((score, place))
        
        # Сортируем по убыванию скора, затем по времени (evening приоритетнее), затем по имени
        scored_places.sort(key=lambda x: (x[0], x[1].typical_time == "evening", x[1].name), reverse=True)
        return [place for score, place in scored_places]
    
    def create_week_plan(self, category_ids: List[str]) -> WeekPlan:
        """Создает план на неделю"""
        # Получаем теги из выбранных категорий
        target_tags = self.get_selected_tags(category_ids)
        
        # Фильтруем места по тегам и скорим
        filtered_places = [place for place in self.places if place.city == "Bangkok"]
        scored_places = self.score_places(filtered_places, target_tags)
        
        # Дни недели
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # Создаем план (максимум 1 активность в день)
        day_plans = []
        used_places = set()
        
        for day in days:
            # Ищем неиспользованное место
            for place in scored_places:
                if place.id not in used_places:
                    day_plans.append(DayPlan(day=day, activity=place))
                    used_places.add(place.id)
                    break
        
        return WeekPlan(days=day_plans, total_activities=len(day_plans))
    
    def format_plan(self, plan: WeekPlan) -> str:
        """Форматирует план для вывода"""
        if not plan.days:
            return "No activities found for your preferences."
        
        result = "🌆 YOUR WEEK IN BANGKOK\n"
        result += "=" * 40 + "\n\n"
        
        for day in plan.days:
            activity = day.activity
            time_emoji = "🌅" if activity.typical_time == "day" else "🌙"
            result += f"{time_emoji} **{day.day}**: {activity.name}\n"
            result += f"   Tags: {', '.join(activity.tags)}\n\n"
        
        result += f"🎯 Total: {plan.total_activities} activities planned"
        return result
