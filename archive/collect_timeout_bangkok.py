#!/usr/bin/env python3
"""
Collect Places from Time Out Bangkok
Uses existing timeout_bkk.py parser and processes places through integrated pipeline
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Добавляем src в Python path
sys.path.insert(0, str(Path('.') / 'src'))
sys.path.insert(0, str(Path('.') / 'tools'))

from integration import create_places_pipeline
from cache import CacheConfig
from fetchers.timeout_bkk import fetch as fetch_timeout_bkk


def main():
    """Main function to collect places from Time Out Bangkok."""
    print("🚀 Starting Time Out Bangkok Places Collection...")
    print("=" * 60)
    
    try:
        # Инициализация интегрированного пайплайна
        print("🔧 Initializing integrated pipeline...")
        pipeline = initialize_pipeline()
        if not pipeline:
            print("❌ Failed to initialize pipeline")
            return 1
        
        # Сбор мест из Time Out Bangkok
        print("📡 Collecting places from Time Out Bangkok...")
        places = collect_timeout_places()
        
        if not places:
            print("❌ No places collected")
            return 1
        
        print(f"📊 Collected {len(places)} places from Time Out Bangkok")
        
        # Обработка мест через пайплайн
        print("🔗 Processing places through pipeline...")
        results = process_places_through_pipeline(pipeline, places)
        
        # Анализ результатов
        print("📈 Analyzing results...")
        analyze_results(results)
        
        # Сохранение результатов
        print("💾 Saving results...")
        save_results(results)
        
        # Очистка
        print("🧹 Cleaning up...")
        pipeline.close()
        
        print("✅ Time Out Bangkok collection completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Error in collection: {e}")
        import traceback
        traceback.print_exc()
        return 1


def initialize_pipeline():
    """Initialize the integrated places pipeline."""
    try:
        # Конфигурация Redis Cloud
        redis_config = CacheConfig(
            host="redis-14374.crce194.ap-seast-1-1.ec2.redns.redis-cloud.com",
            port=14374,
            password="G0vadDS1N9IaEoqQLukwSEGdAHUuPiaW",
            db=0,
            default_ttl=7 * 24 * 3600,
            long_ttl=14 * 24 * 3600,
            key_prefix="v1:places:timeout_bangkok"
        )
        
        # Создаем пайплайн
        pipeline = create_places_pipeline(
            db_path="data/timeout_bangkok_places.db",
            redis_config=redis_config,
            min_quality_score=0.7,
            require_photos=True
        )
        
        print("   ✓ Pipeline initialized successfully")
        return pipeline
        
    except Exception as e:
        print(f"   ❌ Pipeline initialization failed: {e}")
        return None


def collect_timeout_places():
    """Collect places from Time Out Bangkok using existing parser."""
    try:
        print("   📡 Fetching from Time Out Bangkok...")
        
        # Категории для сбора
        categories = [
            "food", "markets_fairs", "yoga_wellness",
            "live_music_gigs", "jazz_blues", "rooftops_bars",
            "workshops", "parks_walks"
        ]
        
        all_places = []
        
        for category in categories:
            print(f"     • Collecting from category: {category}")
            try:
                places = fetch_timeout_bkk(cat_id=category)
                if places:
                    print(f"       ✓ Collected {len(places)} places from {category}")
                    all_places.extend(places)
                else:
                    print(f"       ⚠️ No places from {category}")
                
                # Пауза между категориями
                time.sleep(2)
                
            except Exception as e:
                print(f"       ✗ Error collecting from {category}: {e}")
                continue
        
        print(f"   📊 Total places collected: {len(all_places)}")
        return all_places
        
    except Exception as e:
        print(f"   ❌ Collection failed: {e}")
        return []


def process_places_through_pipeline(pipeline, places):
    """Process collected places through the integrated pipeline."""
    try:
        print("   🔗 Processing places through pipeline...")
        
        # Конвертируем места в формат для пайплайна
        pipeline_places = convert_to_pipeline_format(places)
        
        # Обрабатываем через пайплайн
        results = pipeline.process_batch(pipeline_places)
        
        print(f"   ✓ Pipeline processing completed: {len(results)} results")
        return results
        
    except Exception as e:
        print(f"   ❌ Pipeline processing failed: {e}")
        return []


def convert_to_pipeline_format(places):
    """Convert Time Out places to pipeline format."""
    pipeline_places = []
    
    for i, place in enumerate(places):
        try:
            # Создаем уникальный ID
            place_id = f"timeout_{i+1}_{int(time.time())}"
            
            # Извлекаем адрес из venue
            address = place.get('venue', '')
            if not address:
                address = 'Bangkok, Thailand'  # Default address
            
            # Определяем флаги на основе категории и тегов
            flags = []
            category = place.get('category_hint', 'events')
            
            if category in ['food', 'restaurants']:
                flags.extend(['food_dining', 'restaurants'])
            elif category in ['bars', 'nightlife']:
                flags.extend(['nightlife', 'bars'])
            elif category in ['attractions', 'things-to-do']:
                flags.extend(['attractions', 'things_to_do'])
            elif category in ['shopping', 'markets']:
                flags.extend(['shopping', 'markets'])
            
            # Добавляем флаги из тегов
            tags = place.get('tags', [])
            if 'Picks' in tags:
                flags.append('editor_picks')
            
            # Создаем фото
            photos = []
            image_url = place.get('image')
            if image_url:
                photos.append({
                    'url': image_url,
                    'width': 1200,
                    'height': 800
                })
            
            # Конвертируем в формат пайплайна
            pipeline_place = {
                'id': place_id,
                'name': place.get('title', 'Unknown Place'),
                'city': 'Bangkok',
                'domain': 'timeout.com',
                'url': place.get('url', ''),
                'description': place.get('desc', ''),
                'address': address,
                'geo_lat': None,  # Time Out не предоставляет координаты
                'geo_lng': None,
                'tags': tags,
                'flags': flags,
                'phone': None,
                'email': None,
                'website': None,
                'hours': None,
                'price_level': None,
                'rating': None,
                'photos': photos,
                'image_url': image_url,
                'quality_score': 0.85,  # Базовый score для Time Out
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            }
            
            pipeline_places.append(pipeline_place)
            
        except Exception as e:
            print(f"     ⚠️ Error converting place {i}: {e}")
            continue
    
    print(f"     ✓ Converted {len(pipeline_places)} places to pipeline format")
    return pipeline_places


def analyze_results(results):
    """Analyze pipeline processing results."""
    try:
        print("   📈 Analyzing pipeline results...")
        
        # Статистика по статусам
        status_counts = {}
        for result in results:
            status = result.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("     Pipeline Results:")
        for status, count in status_counts.items():
            print(f"       • {status}: {count} places")
        
        # Детали по местам
        print("     Place Details:")
        for result in results:
            if result.status == 'new':
                print(f"       ✓ {result.name}")
                if result.quality_metrics:
                    print(f"         Quality Score: {result.quality_metrics.get_overall_score()}")
                if result.search_indexed:
                    print(f"         Search Indexed: Yes")
                if result.cache_updated:
                    print(f"         Cache Updated: Yes")
            elif result.status == 'duplicate':
                print(f"       🔄 {result.name} (Duplicate)")
                if result.dedup_info:
                    print(f"         Duplicate of: {result.dedup_info.get('duplicate_id')}")
            elif result.status == 'rejected':
                print(f"       ❌ {result.name} (Rejected)")
                if result.errors:
                    print(f"         Reasons: {', '.join(result.errors)}")
        
        # Статистика пайплайна
        pipeline_stats = results[0].__dict__.get('_pipeline', {}).get('stats', {}) if results else {}
        if pipeline_stats:
            print("     Pipeline Statistics:")
            print(f"       Total Processed: {pipeline_stats.get('total_processed', 0)}")
            print(f"       New Places: {pipeline_stats.get('new_places', 0)}")
            print(f"       Duplicates: {pipeline_stats.get('duplicates', 0)}")
            print(f"       Rejected: {pipeline_stats.get('rejected', 0)}")
            print(f"       Errors: {pipeline_stats.get('errors', 0)}")
        
        print("   ✓ Results analysis completed")
        
    except Exception as e:
        print(f"   ❌ Results analysis failed: {e}")


def save_results(results):
    """Save collection results to file."""
    try:
        print("   💾 Saving results...")
        
        # Создаем директорию для результатов
        results_dir = Path('results')
        results_dir.mkdir(exist_ok=True)
        
        # Сохраняем детальные результаты
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = results_dir / f'timeout_bangkok_collection_{timestamp}.json'
        
        # Конвертируем результаты в JSON-совместимый формат
        json_results = []
        for result in results:
            json_result = {
                'place_id': result.place_id,
                'name': result.name,
                'city': result.city,
                'status': result.status,
                'dedup_info': result.dedup_info,
                'quality_metrics': result.quality_metrics.get_overall_score() if result.quality_metrics else None,
                'search_indexed': result.search_indexed,
                'cache_updated': result.cache_updated,
                'processing_time': result.processing_time,
                'errors': result.errors
            }
            json_results.append(json_result)
        
        # Сохраняем в файл
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, indent=2, ensure_ascii=False)
        
        print(f"     ✓ Results saved to {results_file}")
        
        # Сохраняем краткий отчет
        report_file = results_dir / f'timeout_bangkok_report_{timestamp}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("Time Out Bangkok Collection Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Collection Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Places: {len(results)}\n\n")
            
            # Статистика по статусам
            status_counts = {}
            for result in results:
                status = result.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            f.write("Results Summary:\n")
            for status, count in status_counts.items():
                f.write(f"  {status}: {count} places\n")
            
            f.write("\nDetailed Results:\n")
            for result in results:
                f.write(f"\n{result.name} ({result.status})\n")
                if result.quality_metrics:
                    f.write(f"  Quality Score: {result.quality_metrics.get_overall_score()}\n")
                if result.errors:
                    f.write(f"  Errors: {', '.join(result.errors)}\n")
        
        print(f"     ✓ Report saved to {report_file}")
        
    except Exception as e:
        print(f"   ❌ Results saving failed: {e}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
