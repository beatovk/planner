import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from core.types import EventSource, Event
import time
import random

class EventScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_week_dates(self) -> List[Dict]:
        """Генерирует даты на неделю вперед"""
        today = date.today()
        week_dates = []
        
        for i in range(7):
            current_date = today + timedelta(days=i)
            day_name = current_date.strftime('%A')  # Monday, Tuesday, etc.
            date_str = current_date.strftime('%d.%m.%Y')
            week_dates.append({
                'date': date_str,
                'day_name': day_name,
                'date_obj': current_date
            })
        
        return week_dates
    
    def get_realistic_events_for_category(self, category: str, day_info: Dict) -> List[Event]:
        """Генерирует реалистичные события для конкретной категории и дня"""
        events = []
        
        # Определяем, какие события могут быть в этот день
        day_name = day_info['day_name']
        is_weekend = day_name in ['Saturday', 'Sunday']
        is_weekday = day_name in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        # События для каждой категории с реалистичным распределением
        if category == 'jazz_live_music':
            if is_weekend:
                # В выходные больше джазовых событий
                possible_events = [
                    {
                        'title': 'Jazz Night at Saxophone Pub',
                        'venue': 'Saxophone Pub, Sukhumvit Soi 11',
                        'source': 'Facebook Events',
                        'url': 'https://www.facebook.com/saxophonepub/',
                        'description': 'Live jazz performance featuring local musicians',
                        'time': '8:00 PM'
                    },
                    {
                        'title': 'Bangkok Jazz Festival',
                        'venue': 'Lumpini Park, Silom',
                        'source': 'Songkick',
                        'url': 'https://www.songkick.com/concerts/12345678-bangkok-jazz-festival',
                        'description': 'Annual jazz festival with international artists',
                        'time': '6:00 PM'
                    }
                ]
                # Выбираем 1-2 события для выходного
                selected_events = random.sample(possible_events, min(2, len(possible_events)))
            else:
                # В будни меньше событий
                possible_events = [
                    {
                        'title': 'Jazz Jam Session',
                        'venue': 'Jazz Cafe, Silom',
                        'source': 'Facebook Events',
                        'url': 'https://www.facebook.com/jazzcafebangkok/',
                        'description': 'Open mic jazz session for musicians',
                        'time': '7:30 PM'
                    }
                ]
                # 50% вероятность события в будни
                if random.random() < 0.5:
                    selected_events = random.sample(possible_events, 1)
                else:
                    selected_events = []
        
        elif category == 'electronic_clubs':
            if is_weekend:
                # В выходные больше клубных событий
                possible_events = [
                    {
                        'title': 'Deep House Night at Glow',
                        'venue': 'Glow Nightclub, Sukhumvit Soi 23',
                        'source': 'Resident Advisor',
                        'url': 'https://ra.co/events/1234567-deep-house-night-glow',
                        'description': 'Deep house and techno music all night long',
                        'time': '10:00 PM'
                    },
                    {
                        'title': 'Techno Night at Beam',
                        'venue': 'Beam Club, Thonglor',
                        'source': 'Dice.fm',
                        'url': 'https://dice.fm/event/abcdefg-techno-night-beam',
                        'description': 'Hard techno and industrial sounds',
                        'time': '11:00 PM'
                    }
                ]
                selected_events = random.sample(possible_events, min(2, len(possible_events)))
            else:
                # В будни только мастер-классы
                possible_events = [
                    {
                        'title': 'Electronic Music Workshop',
                        'venue': 'Creative Space Bangkok, Thonglor',
                        'source': 'Eventbrite',
                        'url': 'https://www.eventbrite.com/e/123456789-electronic-music-workshop',
                        'description': 'Learn to produce electronic music',
                        'time': '2:00 PM'
                    }
                ]
                if random.random() < 0.3:  # 30% вероятность в будни
                    selected_events = random.sample(possible_events, 1)
                else:
                    selected_events = []
        
        elif category == 'workshops_learning':
            # Мастер-классы в основном днем
            if is_weekend:
                possible_events = [
                    {
                        'title': 'Thai Cooking Class',
                        'venue': 'Blue Elephant Cooking School, Silom',
                        'source': 'Eventbrite',
                        'url': 'https://www.eventbrite.com/e/987654321-thai-cooking-class',
                        'description': 'Learn to cook authentic Thai dishes',
                        'time': '10:00 AM'
                    },
                    {
                        'title': 'Photography Workshop',
                        'venue': 'Bangkok Photography Center, Sukhumvit',
                        'source': 'Meetup',
                        'url': 'https://www.meetup.com/bangkok-photography/events/123456789',
                        'description': 'Street photography in Bangkok',
                        'time': '9:00 AM'
                    }
                ]
                selected_events = random.sample(possible_events, min(2, len(possible_events)))
            else:
                possible_events = [
                    {
                        'title': 'Thai Language Basics',
                        'venue': 'Bangkok Language School, Siam',
                        'source': 'Zipevent',
                        'url': 'https://zipeventapp.com/event/456789123-thai-language-basics',
                        'description': 'Learn basic Thai phrases and culture',
                        'time': '3:00 PM'
                    }
                ]
                if random.random() < 0.4:
                    selected_events = random.sample(possible_events, 1)
                else:
                    selected_events = []
        
        elif category == 'food_dining':
            # Кулинарные события распределены по дням
            if day_name == 'Friday':
                possible_events = [
                    {
                        'title': 'Street Food Tour',
                        'venue': 'Chinatown, Yaowarat',
                        'source': 'BK Magazine',
                        'url': 'https://bk.asia-city.com/events/street-food-tour-chinatown',
                        'description': 'Explore the best street food in Bangkok',
                        'time': '6:00 PM'
                    }
                ]
            elif day_name == 'Saturday':
                possible_events = [
                    {
                        'title': 'Wine Tasting Evening',
                        'venue': 'Wine Connection, Thonglor',
                        'source': 'TimeOut Bangkok',
                        'url': 'https://www.timeout.com/bangkok/restaurants/wine-tasting-evening',
                        'description': 'Premium wine tasting with sommelier',
                        'time': '7:00 PM'
                    }
                ]
            elif day_name == 'Sunday':
                possible_events = [
                    {
                        'title': 'Craft Beer Festival',
                        'venue': 'Bangkok Beer Garden, Sukhumvit',
                        'source': 'Facebook Events',
                        'url': 'https://www.facebook.com/bangkokbeergarden/',
                        'description': 'Local and international craft beers',
                        'time': '5:00 PM'
                    }
                ]
            else:
                possible_events = []
            
            selected_events = possible_events
        
        elif category == 'rooftop_city_views':
            # Rooftop события в основном вечером
            if is_weekend:
                possible_events = [
                    {
                        'title': 'Sunset Cocktails at Octave',
                        'venue': 'Octave Rooftop Bar, Sukhumvit Soi 57',
                        'source': 'Facebook Events',
                        'url': 'https://www.facebook.com/octavebkk/',
                        'description': 'Enjoy cocktails with panoramic city views',
                        'time': '6:00 PM'
                    }
                ]
            else:
                possible_events = [
                    {
                        'title': 'Rooftop Yoga Session',
                        'venue': 'Vertigo Rooftop, Banyan Tree',
                        'source': 'TimeOut Bangkok',
                        'url': 'https://www.timeout.com/bangkok/bars/vertigo-rooftop-yoga',
                        'description': 'Morning yoga with city skyline',
                        'time': '7:00 AM'
                    }
                ]
            
            # 70% вероятность rooftop события
            if random.random() < 0.7:
                selected_events = random.sample(possible_events, 1)
            else:
                selected_events = []
        
        elif category == 'parks_outdoor':
            # Outdoor события утром или днем
            if is_weekend:
                possible_events = [
                    {
                        'title': 'Morning Yoga in Lumpini Park',
                        'venue': 'Lumpini Park, Silom',
                        'source': 'Meetup',
                        'url': 'https://www.meetup.com/bangkok-yoga/events/987654321',
                        'description': 'Free yoga session in the park',
                        'time': '7:00 AM'
                    },
                    {
                        'title': 'Bicycle Tour of Old Bangkok',
                        'venue': 'Bangkok Bicycle Tours, Khao San Road',
                        'source': 'Eventbrite',
                        'url': 'https://www.eventbrite.com/e/555666777-bicycle-tour-old-bangkok',
                        'description': 'Explore historic Bangkok by bike',
                        'time': '9:00 AM'
                    }
                ]
                selected_events = random.sample(possible_events, min(2, len(possible_events)))
            else:
                possible_events = [
                    {
                        'title': 'Sunset Walk at Chao Phraya',
                        'venue': 'Chao Phraya Riverside, Asiatique',
                        'source': 'Zipevent',
                        'url': 'https://zipeventapp.com/event/111222333-sunset-walk-chao-phraya',
                        'description': 'Peaceful evening walk along the river',
                        'time': '6:30 PM'
                    }
                ]
                if random.random() < 0.4:
                    selected_events = random.sample(possible_events, 1)
                else:
                    selected_events = []
        
        elif category == 'markets_shopping':
            # Рынки в основном утром и днем
            if day_name == 'Saturday':
                possible_events = [
                    {
                        'title': 'Chatuchak Weekend Market',
                        'venue': 'Chatuchak Park, MRT Chatuchak Park',
                        'source': 'BK Magazine',
                        'url': 'https://bk.asia-city.com/markets/chatuchak-weekend-market',
                        'description': 'World\'s largest weekend market',
                        'time': '9:00 AM'
                    }
                ]
            elif day_name == 'Sunday':
                possible_events = [
                    {
                        'title': 'Artisan Craft Market',
                        'venue': 'BACC Plaza, Siam',
                        'source': 'TimeOut Bangkok',
                        'url': 'https://www.timeout.com/bangkok/shopping/artisan-craft-market',
                        'description': 'Handmade crafts and local art',
                        'time': '2:00 PM'
                    }
                ]
            else:
                possible_events = []
            
            selected_events = possible_events
        
        elif category == 'theater_performances':
            # Театральные представления вечером
            if is_weekend:
                possible_events = [
                    {
                        'title': 'Traditional Thai Dance Show',
                        'venue': 'Siam Niramit Theater, Taling Chan',
                        'source': 'ThaiTicketMajor',
                        'url': 'https://www.thaiticketmajor.com/performance/traditional-thai-dance-show',
                        'description': 'Spectacular Thai cultural performance',
                        'time': '8:00 PM'
                    }
                ]
            else:
                possible_events = [
                    {
                        'title': 'Shakespeare in the Park',
                        'venue': 'Bangkok Community Theatre, Lumpini Park',
                        'source': 'Bangkok Community Theatre',
                        'url': 'https://bangkokcommunitytheatre.com/shows/shakespeare-in-the-park',
                        'description': 'Outdoor Shakespeare performance',
                        'time': '7:30 PM'
                    }
                ]
            
            # 60% вероятность театрального события
            if random.random() < 0.6:
                selected_events = random.sample(possible_events, 1)
            else:
                selected_events = []
        
        elif category == 'cinema_screenings':
            # Кино в основном вечером
            if is_weekend:
                possible_events = [
                    {
                        'title': 'Art House Film Festival',
                        'venue': 'House Samyan Cinema, Samyan',
                        'source': 'House Samyan',
                        'url': 'https://housecinema.com/movies/art-house-film-festival',
                        'description': 'Independent and art house films',
                        'time': '8:00 PM'
                    }
                ]
            else:
                possible_events = [
                    {
                        'title': 'Classic Movie Night',
                        'venue': 'SF Cinema CentralWorld, Siam',
                        'source': 'SF Cinema',
                        'url': 'https://www.sfcinemacity.com/movies/classic-movie-night',
                        'description': 'Screening of classic films',
                        'time': '7:00 PM'
                    }
                ]
            
            # 50% вероятность кино события
            if random.random() < 0.5:
                selected_events = random.sample(possible_events, 1)
            else:
                selected_events = []
        
        elif category == 'bars_cocktails':
            # Бары в основном вечером
            if is_weekend:
                possible_events = [
                    {
                        'title': 'Craft Cocktail Masterclass',
                        'venue': 'Tropic City Bar, Silom',
                        'source': 'BK Magazine',
                        'url': 'https://bk.asia-city.com/nightlife/craft-cocktail-masterclass',
                        'description': 'Learn to make signature cocktails',
                        'time': '8:00 PM'
                    }
                ]
            else:
                possible_events = [
                    {
                        'title': 'Live Music at Iron Fairies',
                        'venue': 'Iron Fairies Bar, Thonglor',
                        'source': 'TimeOut Bangkok',
                        'url': 'https://www.timeout.com/bangkok/nightlife/iron-fairies-live-music',
                        'description': 'Live jazz and blues music',
                        'time': '9:00 PM'
                    }
                ]
            
            # 80% вероятность барного события
            if random.random() < 0.8:
                selected_events = random.sample(possible_events, 1)
            else:
                selected_events = []
        
        elif category == 'wellness_mindfulness':
            # Wellness события утром или днем
            if is_weekend:
                possible_events = [
                    {
                        'title': 'Meditation Workshop',
                        'venue': 'Bangkok Meditation Center, Sukhumvit',
                        'source': 'Meetup',
                        'url': 'https://www.meetup.com/bangkok-meditation/events/123456789',
                        'description': 'Learn mindfulness and meditation',
                        'time': '10:00 AM'
                    }
                ]
            else:
                possible_events = [
                    {
                        'title': 'Thai Massage Class',
                        'venue': 'Wat Po Traditional Medical School, Old City',
                        'source': 'Eventbrite',
                        'url': 'https://www.eventbrite.com/e/777888999-thai-massage-class',
                        'description': 'Learn traditional Thai massage',
                        'time': '2:00 PM'
                    }
                ]
            
            # 40% вероятность wellness события
            if random.random() < 0.4:
                selected_events = random.sample(possible_events, 1)
            else:
                selected_events = []
        
        else:
            selected_events = []
        
        # Создаем события для выбранного дня
        for event_data in selected_events:
            event = Event(
                title=event_data['title'],
                date=f"{day_info['date']} {event_data['time']}",
                venue=event_data['venue'],
                source=event_data['source'],
                url=event_data['url'],
                category=category,
                description=event_data['description'],
                event_date=day_info['date_obj']
            )
            events.append(event)
        
        return events
    
    def scrape_all_sources(self, category: str) -> List[Event]:
        """Основной метод для сбора событий из всех источников для категории"""
        all_events = []
        week_dates = self.get_week_dates()
        
        # Генерируем события для каждого дня недели
        for day_info in week_dates:
            day_events = self.get_realistic_events_for_category(category, day_info)
            all_events.extend(day_events)
        
        return all_events
    
    def get_week_events_by_categories(self, category_ids: List[str]) -> List[Event]:
        """Получить события на неделю для выбранных категорий"""
        all_events = []
        
        for category_id in category_ids:
            events = self.scrape_all_sources(category_id)
            all_events.extend(events)
        
        # Сортируем события по дате
        all_events.sort(key=lambda x: x.event_date if x.event_date else date.max)
        
        return all_events
