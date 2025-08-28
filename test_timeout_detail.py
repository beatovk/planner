#!/usr/bin/env python3
import httpx
import asyncio
from bs4 import BeautifulSoup

async def test_timeout_detail():
    # Test the "Art exhibitions this August" page
    url = "https://www.timeout.com/bangkok/art/art-exhibitions-this-august"
    print(f"Testing detail page: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            print(f"Length: {len(response.text)}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for actual event listings
            print("\n🔍 Looking for event listings...")
            
            # Check for different event selectors
            event_selectors = [
                ".event-listing",
                ".event-item", 
                ".listing-item",
                ".event",
                ".item",
                "li",
                ".event-card"
            ]
            
            for selector in event_selectors:
                events = soup.select(selector)
                if events:
                    print(f"  {selector}: {len(events)} found")
                    
                    # Check first few for event-like content
                    for i, event in enumerate(events[:3]):
                        text = event.get_text(strip=True)
                        if len(text) > 20:  # Meaningful content
                            print(f"    Event {i+1}: {text[:100]}...")
                            
                            # Check for dates
                            date_patterns = [
                                r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b',
                                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\b',
                                r'\b\d{4}-\d{2}-\d{2}\b',
                                r'\b(?:Today|Tomorrow|This weekend|Next week)\b'
                            ]
                            
                            import re
                            for pattern in date_patterns:
                                matches = re.findall(pattern, text, re.IGNORECASE)
                                if matches:
                                    print(f"      📅 Date found: {matches[0]}")
                                    break
                            
                            # Check for venue/location
                            if any(word in text.lower() for word in ['bangkok', 'gallery', 'museum', 'center', 'plaza']):
                                print(f"      🏛️ Location mentioned")
                            
                            break
                    break
            
            # Check for JSON-LD structured data
            print("\n🔍 Checking for JSON-LD data...")
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
                            else:
                                print(f"    Script {i+1}: Type: {data.get('@type', 'Unknown')}")
                    except:
                        print(f"    Script {i+1}: Invalid JSON")
            else:
                print("  ❌ No JSON-LD data found")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_timeout_detail())
