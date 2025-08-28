#!/usr/bin/env python3
import httpx
import asyncio
from bs4 import BeautifulSoup

async def test_timeout_detailed():
    url = "https://www.timeout.com/bangkok/things-to-do"
    print(f"Testing {url}")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            print(f"Length: {len(response.text)}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for different card selectors
            selectors = [
                "article.tile",
                ".card", 
                ".event-card",
                ".listing-card",
                "article",
                ".article-card",
                ".feature-card",
                ".tile",
                ".item"
            ]
            
            print("\n🔍 Testing selectors:")
            for selector in selectors:
                cards = soup.select(selector)
                print(f"  {selector}: {len(cards)} found")
                if len(cards) > 0:
                    # Show first card structure
                    first = cards[0]
                    print(f"    First card: {first.name} with classes: {first.get('class', [])}")
                    
                    # Check for title
                    title_els = first.select("h1, h2, h3, .title, .card-title")
                    if title_els:
                        print(f"    Title found: {title_els[0].get_text(strip=True)[:50]}...")
                    else:
                        print(f"    ❌ No title found")
                    
                    # Check for links
                    links = first.select("a")
                    if links:
                        print(f"    Link found: {links[0].get('href', '')[:50]}...")
                    else:
                        print(f"    ❌ No links found")
                    break
            
            # Check for specific content patterns
            print("\n🔍 Content analysis:")
            if "things to do" in response.text.lower():
                print("  ✅ 'Things to do' text found")
            else:
                print("  ❌ 'Things to do' text not found")
                
            if "bangkok" in response.text.lower():
                print("  ✅ 'Bangkok' text found")
            else:
                print("  ❌ 'Bangkok' text not found")
                
            # Check for JavaScript rendering
            if "loading" in response.text.lower():
                print("  ⚠️ Loading indicators found - might be JS-rendered")
                
            if "react" in response.text.lower() or "vue" in response.text.lower():
                print("  ⚠️ JavaScript framework detected")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_timeout_detailed())
