#!/usr/bin/env python3
import httpx
import asyncio

async def test_timeout():
    url = "https://www.timeout.com/bangkok/things-to-do"
    print(f"Testing {url}")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            print(f"Length: {len(response.text)}")
            print("Content preview:")
            print(response.text[:1000])
            
            # Check if it's blocked
            if "blocked" in response.text.lower() or "captcha" in response.text.lower():
                print("❌ Site is blocking requests!")
            elif "timeout" in response.text.lower():
                print("✅ Site content found")
            else:
                print("⚠️ Unknown response content")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_timeout())
