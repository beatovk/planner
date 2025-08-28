#!/usr/bin/env python3
"""
CLI for managing Timeout Bangkok places.
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path

# Добавляем корневую директорию в Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.wp_places.timeout_service import TimeoutPlacesService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_parser(args):
    """Test the Timeout parser."""
    print("🧪 Testing Timeout Bangkok parser...")
    
    async with TimeoutPlacesService() as service:
        result = await service.test_parser(
            category=args.category,
            limit=args.limit
        )
        
        if result['success']:
            print(f"✅ Parser test successful!")
            print(f"📰 Category: {result['category']}")
            print(f"🔗 URL tested: {result['url_tested']}")
            print(f"🏪 Places found: {result['places_found']}")
            
            if result['sample_data']:
                print(f"\n📋 Sample places (showing {len(result['sample_data'])}):")
                for i, place in enumerate(result['sample_data'], 1):
                    print(f"\n{i}. {place['name']}")
                    print(f"   📍 Area: {place['area'] or 'Unknown'}")
                    print(f"   💰 Price level: {place['price_level']}")
                    print(f"   🏷️  Flags: {', '.join(place['flags'])}")
                    print(f"   📝 Description: {place['description']}")
        else:
            print(f"❌ Parser test failed: {result['error']}")
            if 'available_categories' in result:
                print(f"Available categories: {', '.join(result['available_categories'])}")

async def refresh_places(args):
    """Refresh places from Timeout Bangkok."""
    print("🔄 Refreshing places from Timeout Bangkok...")
    
    categories = args.categories.split(',') if args.categories else None
    
    if categories:
        print(f"📂 Processing categories: {', '.join(categories)}")
    else:
        print("📂 Processing all available categories")
    
    async with TimeoutPlacesService() as service:
        stats = await service.refresh_places_from_timeout(categories)
        
        print(f"\n📊 Refresh completed!")
        print(f"⏱️  Duration: {stats['duration_seconds']:.2f} seconds")
        print(f"📂 Categories processed: {stats['categories_processed']}")
        print(f"📰 Articles processed: {stats['articles_processed']}")
        print(f"🏪 Places extracted: {stats['places_extracted']}")
        print(f"💾 Places saved: {stats['places_saved']}")
        
        if stats['errors']:
            print(f"\n❌ Errors encountered:")
            for error in stats['errors']:
                print(f"   - {error}")

async def get_stats(args):
    """Get statistics about Timeout places."""
    print("📊 Getting Timeout places statistics...")
    
    async with TimeoutPlacesService() as service:
        stats = await service.get_timeout_places_stats()
        
        if 'error' in stats:
            print(f"❌ Error: {stats['error']}")
            return
        
        print(f"\n📊 Timeout Places Statistics:")
        print(f"🏪 Total places: {stats['total_places']}")
        print(f"🕐 Last updated: {stats['last_updated']}")
        
        if stats['by_category']:
            print(f"\n📂 By category:")
            for category, count in sorted(stats['by_category'].items()):
                print(f"   {category}: {count}")
        
        if stats['by_area']:
            print(f"\n📍 By area:")
            for area, count in sorted(stats['by_area'].items()):
                print(f"   {area}: {count}")

async def list_categories(args):
    """List available categories."""
    print("📂 Available Timeout Bangkok categories:")
    
    async with TimeoutPlacesService() as service:
        categories = list(service.parser.categories.keys())
        
        for i, category in enumerate(categories, 1):
            urls = service.parser.categories[category]
            print(f"{i}. {category}")
            print(f"   URLs: {', '.join(urls)}")
            print()

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="CLI for managing Timeout Bangkok places",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test parser with food_dining category
  python timeout_places_cli.py test --category food_dining --limit 5
  
  # Refresh all places
  python timeout_places_cli.py refresh
  
  # Refresh specific categories
  python timeout_places_cli.py refresh --categories food_dining,art_exhibits
  
  # Get statistics
  python timeout_places_cli.py stats
  
  # List available categories
  python timeout_places_cli.py categories
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Test command
    test_parser_cmd = subparsers.add_parser('test', help='Test the Timeout parser')
    test_parser_cmd.add_argument('--category', default='food_dining', 
                                help='Category to test (default: food_dining)')
    test_parser_cmd.add_argument('--limit', type=int, default=3,
                                help='Number of places to show (default: 3)')
    
    # Refresh command
    refresh_parser_cmd = subparsers.add_parser('refresh', help='Refresh places from Timeout')
    refresh_parser_cmd.add_argument('--categories', 
                                   help='Comma-separated list of categories to process')
    
    # Stats command
    subparsers.add_parser('stats', help='Get Timeout places statistics')
    
    # Categories command
    subparsers.add_parser('categories', help='List available categories')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'test':
            asyncio.run(test_parser(args))
        elif args.command == 'refresh':
            asyncio.run(refresh_places(args))
        elif args.command == 'stats':
            asyncio.run(get_stats(args))
        elif args.command == 'categories':
            asyncio.run(list_categories(args))
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.error(f"CLI error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
