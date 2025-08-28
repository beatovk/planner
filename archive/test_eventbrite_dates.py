#!/usr/bin/env python3
import httpx
import asyncio
from bs4 import BeautifulSoup

async def test_eventbrite_dates():
    url = "https://www.eventbrite.com/d/thailand--bangkok/events/"
    print(f"🔍 Анализируем даты в Eventbrite Bangkok: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find event cards
            cards = soup.select(".event-card, [data-testid='event-card'], .eds-event-card")
            if not cards:
                cards = soup.select("article, .card, .item")
            
            print(f"📊 Found {len(cards)} event cards")
            
            # Analyze first few cards for date structure
            for i, card in enumerate(cards[:5]):
                print(f"\n--- Card {i+1} ---")
                
                # Look for all time/date elements
                time_elements = card.find_all("time")
                print(f"  Time elements: {len(time_elements)}")
                
                for j, time_el in enumerate(time_elements):
                    datetime_attr = time_el.get('datetime')
                    text_content = time_el.get_text(strip=True)
                    print(f"    Time {j+1}: datetime='{datetime_attr}', text='{text_content}'")
                
                # Look for date-related classes
                date_classes = [
                    ".eds-event-card__formatted-date",
                    ".event-date",
                    "[data-testid='event-date']",
                    ".eds-text-bs",
                    ".date",
                    ".time"
                ]
                
                for selector in date_classes:
                    date_el = card.select_one(selector)
                    if date_el:
                        text = date_el.get_text(strip=True)
                        if text:
                            print(f"  Date ({selector}): {text}")
                
                # Look for any text that might contain dates
                card_text = card.get_text()
                date_patterns = [
                    r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b',
                    r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b',
                    r'\b\d{4}-\d{2}-\d{2}\b',
                    r'\b(?:Today|Tomorrow|This weekend|Next week)\b',
                    r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b',
                    r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\b'
                ]
                
                import re
                dates_found = []
                for pattern in date_patterns:
                    matches = re.findall(pattern, card_text, re.IGNORECASE)
                    if matches:
                        dates_found.extend(matches[:2])
                
                if dates_found:
                    print(f"  📅 Dates found in text: {', '.join(set(dates_found))}")
                else:
                    print(f"  ❌ No dates found in text")
                
                print("-" * 40)
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_eventbrite_dates())
