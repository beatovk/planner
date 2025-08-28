#!/usr/bin/env python
import os, json, sys
import redis

VERSION = "v2"

def main():
    if len(sys.argv) < 3:
        print("Usage: inspect_cache.py <city> <YYYY-MM-DD> [flag]")
        sys.exit(1)
    city, day = sys.argv[1], sys.argv[2]
    fl = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Проверяем REDIS_URL
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        print("ERROR: REDIS_URL not set")
        sys.exit(1)
    
    try:
        r = redis.from_url(redis_url, decode_responses=True)
        r.ping()  # Проверяем подключение
    except Exception as e:
        print(f"ERROR: Cannot connect to Redis: {e}")
        sys.exit(1)

    print(f"=== Cache Inspection for {city} on {day} ===")
    
    # Проверяем индекс дня
    index_key = f"{VERSION}:{city}:{day}:index"
    index_ttl = r.ttl(index_key)
    print(f"\nINDEX: {index_key}")
    print(f"TTL: {index_ttl}s ({'expired' if index_ttl == -2 else 'no expiry' if index_ttl == -1 else 'active'})")
    
    index_data = r.get(index_key)
    if index_data:
        try:
            index_json = json.loads(index_data)
            print("Data:")
            print(json.dumps(index_json, indent=2))
        except Exception as e:
            print(f"ERROR parsing index JSON: {e}")
            print(f"Raw data: {index_data}")
    else:
        print("No index data found")

    # Если указан флаг, проверяем его
    if fl:
        flag_key = f"{VERSION}:{city}:{day}:flag:{fl}"
        flag_ttl = r.ttl(flag_key)
        print(f"\nFLAG: {flag_key}")
        print(f"TTL: {flag_ttl}s ({'expired' if flag_ttl == -2 else 'no expiry' if flag_ttl == -1 else 'active'})")
        
        flag_data = r.get(flag_key)
        if flag_data:
            try:
                flag_json = json.loads(flag_data)
                print("Data:")
                print(json.dumps(flag_json, indent=2))
            except Exception as e:
                print(f"ERROR parsing flag JSON: {e}")
                print(f"Raw data: {flag_data}")
        else:
            print("No flag data found")
    
    # Показываем все ключи для этого дня
    print(f"\nALL KEYS for {city}:{day}:")
    pattern = f"{VERSION}:{city}:{day}:*"
    keys = r.keys(pattern)
    
    if keys:
        for key in sorted(keys):
            ttl = r.ttl(key)
            ttl_status = 'expired' if ttl == -2 else 'no expiry' if ttl == -1 else f'{ttl}s'
            print(f"  {key} (TTL: {ttl_status})")
    else:
        print("  No keys found")
    
    print(f"\nTotal keys: {len(keys)}")

if __name__ == "__main__":
    main()
