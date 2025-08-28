#!/usr/bin/env python3
import httpx
import asyncio
from bs4 import BeautifulSoup

async def test_bk_magazine():
    url = "https://bk.asia-city.com/things-to-do"
    print(f"Testing BK Magazine: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            print(f"Length: {len(response.text)}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for different content selectors
            selectors = [
                "article",
                ".node",
                ".article",
                ".content",
                ".item"
            ]
            
            print("\n🔍 Testing selectors:")
            for selector in selectors:
                items = soup.select(selector)
                if items:
                    print(f"  {selector}: {len(items)} found")
                    if len(items) > 0:
                        first = items[0]
                        print(f"    First item: {first.name} with classes: {first.get('class', [])}")
                        
                        # Check for title
                        title_els = first.select("h1, h2, h3, .title, .node__title")
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
    asyncio.run(test_bk_magazine())
