#!/usr/bin/env python
from __future__ import annotations
import sys
sys.path.append('..')
from packages.wp_cache.cache import get_cache_client
from packages.wp_cache.redis_safe import get_sync_client

def main():
    if len(sys.argv) != 4:
        print("Usage: redis_diag.py <city> <YYYY-MM-DD> <flag>")
        sys.exit(1)
    city, day, flag = sys.argv[1], sys.argv[2], sys.argv[3]
    
    try:
        r = get_sync_client()
        # Простые ключи для диагностики
        k = f"v2:{city}:{day}:flag:{flag}"
        ks = f"v2:{city}:{day}:flag:{flag}:stale"
        ki = f"v2:{city}:{day}:index"
        
        print("PING:", r.ping())
        print("GET ", k, "=>", r.get(k))
        print("GET ", ks, "=>", r.get(ks))
        print("GET ", ki, "=>", r.get(ki))
    except Exception as e:
        print(f"Redis connection failed: {e}")
        print("Make sure Redis is running and accessible")

if __name__ == "__main__":
    main()
