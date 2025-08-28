#!/usr/bin/env python
from __future__ import annotations
import sys
sys.path.append('..')
from core.cache import ensure_client, make_flag_key, make_index_key

def main():
    if len(sys.argv) != 4:
        print("Usage: redis_diag.py <city> <YYYY-MM-DD> <flag>")
        sys.exit(1)
    city, day, flag = sys.argv[1], sys.argv[2], sys.argv[3]
    r = ensure_client()
    k = make_flag_key(city, day, flag)
    ks = make_flag_key(city, day, flag, stale=True)
    ki = make_index_key(city, day)
    print("PING:", r.ping())
    print("GET ", k, "=>", r.get(k))
    print("GET ", ks, "=>", r.get(ks))
    print("GET ", ki, "=>", r.get(ki))

if __name__ == "__main__":
    main()
