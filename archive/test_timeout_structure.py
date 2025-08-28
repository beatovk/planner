#!/usr/bin/env python3
import httpx
import asyncio
from bs4 import BeautifulSoup

async def test_timeout_structure():
    url = "https://www.timeout.com/bangkok/things-to-do"
    print(f"Testing {url}")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all article.tile elements
            cards = soup.select("article.tile")
            print(f"\n📊 Found {len(cards)} article.tile cards")
            
            for i, card in enumerate(cards[:5]):  # Show first 5
                print(f"\n--- Card {i+1} ---")
                
                # Get card classes
                classes = card.get('class', [])
                print(f"Classes: {classes}")
                
                # Check for title
                title_selectors = ["h1", "h2", "h3", ".title", ".card-title", "a"]
                title_found = False
                for selector in title_selectors:
                    title_el = card.select_one(selector)
                    if title_el:
                        title = title_el.get_text(strip=True)
                        if title and len(title) > 5:
                            print(f"Title ({selector}): {title}")
                            title_found = True
                            break
                
                if not title_found:
                    print("❌ No meaningful title found")
                
                # Check for links
                links = card.select("a")
                if links:
                    for link in links[:2]:  # Show first 2 links
                        href = link.get('href', '')
                        if href and href.startswith('/'):
                            href = f"https://www.timeout.com{href}"
                        print(f"Link: {href}")
                        link_text = link.get_text(strip=True)
                        if link_text:
                            print(f"  Link text: {link_text[:50]}...")
                else:
                    print("❌ No links found")
                
                # Check for images
                images = card.select("img")
                if images:
                    for img in images[:2]:
                        src = img.get('src') or img.get('data-src')
                        if src:
                            print(f"Image: {src}")
                else:
                    print("❌ No images found")
                
                # Check for description/summary
                desc_selectors = ["p", ".summary", ".description", ".excerpt"]
                desc_found = False
                for selector in desc_selectors:
                    desc_el = card.select_one(selector)
                    if desc_el:
                        desc = desc_el.get_text(strip=True)
                        if desc and len(desc) > 10:
                            print(f"Description ({selector}): {desc[:100]}...")
                            desc_found = True
                            break
                
                if not desc_found:
                    print("❌ No description found")
                
                # Check for dates
                date_selectors = ["time", ".date", ".time", "[datetime]"]
                date_found = False
                for selector in date_selectors:
                    date_el = card.select_one(selector)
                    if date_el:
                        date_text = date_el.get_text(strip=True)
                        datetime_attr = date_el.get('datetime')
                        if date_text or datetime_attr:
                            print(f"Date ({selector}): {date_text or datetime_attr}")
                            date_found = True
                            break
                
                if not date_found:
                    print("❌ No date found")
                
                print("-" * 40)
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_timeout_structure())
