#!/usr/bin/env python3
import httpx
import asyncio

async def test_bk_home():
    url = "https://bk.asia-city.com"
    print(f"Testing BK Magazine home: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            print(f"Length: {len(response.text)}")
            print("Content preview:")
            print(response.text[:500])
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_bk_home())
