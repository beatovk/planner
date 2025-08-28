#!/usr/bin/env python3
"""
Детальный тест Eventbrite Bangkok
Проверяем структуру и возможность парсинга событий
"""

import httpx
import asyncio
from bs4 import BeautifulSoup
import re

async def test_eventbrite_detailed():
    url = "https://www.eventbrite.com/d/thailand--bangkok/events/"
    print(f"🔍 Детальный тест Eventbrite Bangkok: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            print(f"Length: {len(response.text)}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for event cards
            print("\n🔍 Ищем карточки событий...")
            
            # Common Eventbrite selectors
            selectors = [
                "[data-testid='event-card']",
                ".eds-event-card",
                ".event-card",
                ".search-event-card",
                "[data-spec='event-card']",
                "article",
                ".eds-l-pad-all-4"
            ]
            
            for selector in selectors:
                cards = soup.select(selector)
                if cards:
                    print(f"  {selector}: {len(cards)} found")
                    if len(cards) > 0:
                        first = cards[0]
                        print(f"    First card: {first.name} with classes: {first.get('class', [])}")
                        
                        # Check for title
                        title_selectors = ["h3", "h2", ".eds-event-card__title", ".event-title", "[data-testid='event-title']"]
                        title_found = False
                        for title_sel in title_selectors:
                            title_el = first.select_one(title_sel)
                            if title_el:
                                title = title_el.get_text(strip=True)
                                if title and len(title) > 5:
                                    print(f"    Title ({title_sel}): {title[:50]}...")
                                    title_found = True
                                    break
                        
                        if not title_found:
                            print(f"    ❌ No title found")
                        
                        # Check for dates
                        date_selectors = [
                            "time", 
                            ".eds-event-card__formatted-date", 
                            ".event-date",
                            "[data-testid='event-date']",
                            ".eds-text-bs"
                        ]
                        date_found = False
                        for date_sel in date_selectors:
                            date_el = first.select_one(date_sel)
                            if date_el:
                                date_text = date_el.get_text(strip=True)
                                datetime_attr = date_el.get('datetime')
                                if date_text or datetime_attr:
                                    print(f"    Date ({date_sel}): {date_text or datetime_attr}")
                                    date_found = True
                                    break
                        
                        if not date_found:
                            print(f"    ❌ No date found")
                        
                        # Check for links
                        links = first.select("a")
                        if links:
                            for link in links[:2]:
                                href = link.get('href', '')
                                if href and 'eventbrite.com' in href:
                                    print(f"    Link: {href}")
                                    break
                        else:
                            print(f"    ❌ No links found")
                        
                        # Check for images
                        images = first.select("img")
                        if images:
                            for img in images[:2]:
                                src = img.get('src') or img.get('data-src')
                                if src:
                                    print(f"    Image: {src[:50]}...")
                                    break
                        else:
                            print(f"    ❌ No images found")
                        
                        break
            
            # Check for JSON-LD structured data
            print("\n🔍 Проверяем JSON-LD данные...")
            jsonld_scripts = soup.find_all('script', type='application/ld+json')
            if jsonld_scripts:
                print(f"  Found {len(jsonld_scripts)} JSON-LD scripts")
                for i, script in enumerate(jsonld_scripts[:2]):
                    try:
                        import json
                        data = json.loads(script.string)
                        if isinstance(data, dict):
                            if data.get('@type') == 'Event':
                                print(f"    Script {i+1}: Event data found!")
                                print(f"      Title: {data.get('name', 'N/A')}")
                                print(f"      Date: {data.get('startDate', 'N/A')}")
                                print(f"      Location: {data.get('location', {}).get('name', 'N/A')}")
                            elif isinstance(data, list) and len(data) > 0:
                                first_item = data[0]
                                if first_item.get('@type') == 'Event':
                                    print(f"    Script {i+1}: Event list found with {len(data)} events!")
                                    print(f"      First event: {first_item.get('name', 'N/A')}")
                            else:
                                print(f"    Script {i+1}: Type: {data.get('@type', 'Unknown')}")
                    except:
                        print(f"    Script {i+1}: Invalid JSON")
            else:
                print("  ❌ No JSON-LD data found")
                
            # Check for specific Eventbrite patterns
            print("\n🔍 Анализ Eventbrite-специфичных паттернов:")
            if "eventbrite" in response.text.lower():
                print("  ✅ 'Eventbrite' text found")
            else:
                print("  ❌ 'Eventbrite' text not found")
                
            if "bangkok" in response.text.lower():
                print("  ✅ 'Bangkok' text found")
            else:
                print("  ❌ 'Bangkok' text not found")
                
            # Check for event count
            event_count_patterns = [
                r'(\d+)\s+events?',
                r'(\d+)\s+results?',
                r'(\d+)\s+items?'
            ]
            
            for pattern in event_count_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                if matches:
                    print(f"  📊 Event count found: {matches[0]}")
                    break
            else:
                print("  ❌ No event count found")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_eventbrite_detailed())
