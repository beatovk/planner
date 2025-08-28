#!/usr/bin/env python
"""
CLI tool for managing places.
"""

import argparse
import json
import sys
from pathlib import Path

# Добавляем корневую директорию в Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.places_service import PlacesService
from core.logging import logger


def main():
    parser = argparse.ArgumentParser(description="Places management CLI")
    parser.add_argument("--city", default="bangkok", help="City name (default: bangkok)")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Команда для получения мест по флагам
    flags_parser = subparsers.add_parser("get-by-flags", help="Get places by flags")
    flags_parser.add_argument("flags", nargs="+", help="Flags to filter by")
    flags_parser.add_argument("--limit", type=int, help="Limit number of places")
    flags_parser.add_argument("--no-cache", action="store_true", help="Skip cache")
    
    # Команда для получения мест по категории
    category_parser = subparsers.add_parser("get-by-category", help="Get places by category")
    category_parser.add_argument("category", help="Category to filter by")
    category_parser.add_argument("--limit", type=int, help="Limit number of places")
    category_parser.add_argument("--no-cache", action="store_true", help="Skip cache")
    
    # Команда для получения всех мест
    all_parser = subparsers.add_parser("get-all", help="Get all places")
    all_parser.add_argument("--limit", type=int, help="Limit number of places")
    all_parser.add_argument("--no-cache", action="store_true", help="Skip cache")
    
    # Команда для прогрева кэша
    warm_parser = subparsers.add_parser("warm-cache", help="Warm up cache")
    warm_parser.add_argument("--flags", nargs="*", help="Flags to warm up (default: all)")
    warm_parser.add_argument("--ttl", type=int, default=3600, help="Cache TTL in seconds")
    
    # Команда для обновления данных
    refresh_parser = subparsers.add_parser("refresh", help="Refresh places data")
    refresh_parser.add_argument("--flags", nargs="*", help="Flags to refresh (default: all)")
    
    # Команда для получения статистики
    stats_parser = subparsers.add_parser("stats", help="Get places statistics")
    
    # Команда для инициализации БД
    init_parser = subparsers.add_parser("init-db", help="Initialize places database")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        service = PlacesService()
        
        if args.command == "get-by-flags":
            places = service.get_places_by_flags(
                args.city, 
                args.flags, 
                args.limit, 
                use_cache=not args.no_cache
            )
            print(f"Found {len(places)} places for flags: {args.flags}")
            for place in places:
                print(f"- {place.name} ({', '.join(place.flags)})")
        
        elif args.command == "get-by-category":
            places = service.get_places_by_category(
                args.city, 
                args.category, 
                args.limit, 
                use_cache=not args.no_cache
            )
            print(f"Found {len(places)} places for category: {args.category}")
            for place in places:
                print(f"- {place.name} ({', '.join(place.flags)})")
        
        elif args.command == "get-all":
            places = service.get_all_places(
                args.city, 
                args.limit, 
                use_cache=not args.no_cache
            )
            print(f"Found {len(places)} total places")
            for place in places:
                print(f"- {place.name} ({', '.join(place.flags)})")
        
        elif args.command == "warm-cache":
            results = service.warm_cache(args.city, args.flags, args.ttl)
            print("Cache warming results:")
            for flag, count in results.items():
                print(f"- {flag}: {count} places")
        
        elif args.command == "refresh":
            results = service.refresh_places(args.city, args.flags)
            print("Refresh results:")
            for flag, count in results.items():
                print(f"- {flag}: {count} places")
        
        elif args.command == "stats":
            stats = service.get_stats(args.city)
            print(json.dumps(stats, indent=2, default=str))
        
        elif args.command == "init-db":
            from core.db_places import init_places_db
            init_places_db()
            print("Places database initialized successfully")
        
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
