#!/usr/bin/env python3
"""
Тест реальных источников событий в Бангкоке
Проверяем популярные сайты событий на доступность и структуру
"""

import httpx
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime

async def test_event_source(name: str, url: str, description: str):
    print(f"\n🔍 Тестируем: {name}")
    print(f"   URL: {url}")
    print(f"   Описание: {description}")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            print(f"   Status: {response.status_code}")
            print(f"   Length: {len(response.text)}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check for event-like content
                event_indicators = [
                    "event", "events", "calendar", "schedule", "ticket", "booking",
                    "concert", "exhibition", "festival", "show", "performance"
                ]
                
                found_indicators = []
                for indicator in event_indicators:
                    if indicator in response.text.lower():
                        found_indicators.append(indicator)
                
                if found_indicators:
                    print(f"   ✅ Event indicators found: {', '.join(found_indicators[:3])}")
                else:
                    print(f"   ❌ No event indicators found")
                
                # Check for dates
                date_patterns = [
                    r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b',
                    r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\b',
                    r'\b\d{4}-\d{2}-\d{2}\b',
                    r'\b(?:Today|Tomorrow|This weekend|Next week)\b'
                ]
                
                import re
                dates_found = []
                for pattern in date_patterns:
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    if matches:
                        dates_found.extend(matches[:2])  # First 2 matches
                
                if dates_found:
                    print(f"   📅 Dates found: {', '.join(set(dates_found))}")
                else:
                    print(f"   ❌ No dates found")
                
                # Check for JavaScript rendering
                if "loading" in response.text.lower():
                    print(f"   ⚠️ Loading indicators - might be JS-rendered")
                    
                if "react" in response.text.lower() or "vue" in response.text.lower():
                    print(f"   ⚠️ JavaScript framework detected")
                    
            else:
                print(f"   ❌ HTTP {response.status_code}")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")

async def test_all_sources():
    print("🚀 Тестируем реальные источники событий в Бангкоке")
    
    sources = [
        {
            "name": "Eventbrite Bangkok",
            "url": "https://www.eventbrite.com/d/thailand--bangkok/events/",
            "description": "Международная платформа событий"
        },
        {
            "name": "Ticketmelon",
            "url": "https://www.ticketmelon.com/",
            "description": "Тайская платформа билетов"
        },
        {
            "name": "Resident Advisor Bangkok",
            "url": "https://ra.co/events/th/bangkok",
            "description": "Электронная музыка и клубные события"
        },
        {
            "name": "Bangkok Art and Culture Centre",
            "url": "https://bacc.or.th/",
            "description": "Официальный сайт BACC"
        },
        {
            "name": "River City Bangkok",
            "url": "https://rivercitybangkok.com/",
            "description": "Торговый центр с галереями"
        },
        {
            "name": "Bangkok Post Events",
            "url": "https://www.bangkokpost.com/events",
            "description": "События от Bangkok Post"
        }
    ]
    
    for source in sources:
        await test_event_source(source["name"], source["url"], source["description"])
        await asyncio.sleep(1)  # Be nice to servers

if __name__ == "__main__":
    asyncio.run(test_all_sources())
