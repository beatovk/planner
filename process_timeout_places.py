#!/usr/bin/env python3
"""
Process Time Out Bangkok Places
Process collected places through the integrated pipeline
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# Добавляем src в Python path
sys.path.insert(0, str(Path('.') / 'src'))

from integration import create_places_pipeline
from cache import CacheConfig


def main():
    """Process Time Out Bangkok places through the pipeline."""
    print("🚀 Processing Time Out Bangkok Places...")
    print("=" * 60)
    
    try:
        # Инициализация интегрированного пайплайна
        print("🔧 Initializing integrated pipeline...")
        pipeline = initialize_pipeline()
        if not pipeline:
            print("❌ Failed to initialize pipeline")
            return 1
        
        # Загрузка собранных мест
        print("📂 Loading collected places...")
        places = load_collected_places()
        
        if not places:
            print("❌ No places to process")
            return 1
        
        print(f"📊 Loaded {len(places)} places for processing")
        
        # Обработка мест через пайплайн
        print("🔗 Processing places through pipeline...")
        results = process_places_through_pipeline(pipeline, places)
        
        # Анализ результатов
        print("📈 Analyzing results...")
        analyze_results(results)
        
        # Сохранение результатов обработки
        print("💾 Saving processing results...")
        save_processing_results(results)
        
        # Очистка
        print("🧹 Cleaning up...")
        pipeline.close()
        
        print("✅ Time Out Bangkok places processing completed!")
        return 0
        
    except Exception as e:
        print(f"❌ Error in processing: {e}")
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


def load_collected_places():
    """Load collected places from the latest file."""
    try:
        # Ищем последний файл с собранными местами
        results_dir = Path('results')
        if not results_dir.exists():
            print("   ❌ Results directory not found")
            return []
        
        # Ищем файлы с pipeline данными
        pipeline_files = list(results_dir.glob('timeout_bangkok_simple_pipeline_*.json'))
        if not pipeline_files:
            print("   ❌ No pipeline files found")
            return []
        
        # Берем самый новый файл
        latest_file = max(pipeline_files, key=lambda x: x.stat().st_mtime)
        print(f"   📁 Loading from: {latest_file.name}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            places = json.load(f)
        
        print(f"   ✓ Loaded {len(places)} places from {latest_file.name}")
        return places
        
    except Exception as e:
        print(f"   ❌ Error loading places: {e}")
        return []


def process_places_through_pipeline(pipeline, places):
    """Process collected places through the integrated pipeline."""
    try:
        print("   🔗 Processing places through pipeline...")
        
        # Обрабатываем места через пайплайн
        results = pipeline.process_batch(places)
        
        print(f"   ✓ Pipeline processing completed: {len(results)} results")
        return results
        
    except Exception as e:
        print(f"   ❌ Pipeline processing failed: {e}")
        return []


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
                if hasattr(result, 'quality_metrics') and result.quality_metrics:
                    print(f"         Quality Score: {result.quality_metrics.get_overall_score()}")
                if hasattr(result, 'search_indexed') and result.search_indexed:
                    print(f"         Search Indexed: Yes")
                if hasattr(result, 'cache_updated') and result.cache_updated:
                    print(f"         Cache Updated: Yes")
            elif result.status == 'duplicate':
                print(f"       🔄 {result.name} (Duplicate)")
                if hasattr(result, 'dedup_info') and result.dedup_info:
                    print(f"         Duplicate of: {result.dedup_info.get('duplicate_id', 'Unknown')}")
            elif result.status == 'rejected':
                print(f"       ❌ {result.name} (Rejected)")
                if hasattr(result, 'errors') and result.errors:
                    print(f"         Reasons: {', '.join(result.errors)}")
        
        print("   ✓ Results analysis completed")
        
    except Exception as e:
        print(f"   ❌ Results analysis failed: {e}")


def save_processing_results(results):
    """Save processing results to files."""
    try:
        # Создаем директорию для результатов
        results_dir = Path('results')
        results_dir.mkdir(exist_ok=True)
        
        # Сохраняем результаты обработки
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Конвертируем результаты в JSON-совместимый формат
        json_results = []
        for result in results:
            json_result = {
                'place_id': getattr(result, 'place_id', 'Unknown'),
                'name': getattr(result, 'name', 'Unknown'),
                'city': getattr(result, 'city', 'Unknown'),
                'status': getattr(result, 'status', 'Unknown'),
                'dedup_info': getattr(result, 'dedup_info', {}),
                'quality_metrics': getattr(result, 'quality_metrics', {}),
                'search_indexed': getattr(result, 'search_indexed', False),
                'cache_updated': getattr(result, 'cache_updated', False),
                'processing_time': getattr(result, 'processing_time', 0),
                'errors': getattr(result, 'errors', [])
            }
            json_results.append(json_result)
        
        # Сохраняем в файл
        results_file = results_dir / f'timeout_bangkok_processing_{timestamp}.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, indent=2, ensure_ascii=False)
        
        print(f"     ✓ Processing results saved to {results_file}")
        
        # Сохраняем краткий отчет
        report_file = results_dir / f'timeout_bangkok_processing_report_{timestamp}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("Time Out Bangkok Processing Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Places Processed: {len(results)}\n\n")
            
            # Статистика по статусам
            status_counts = {}
            for result in results:
                status = result.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            f.write("Processing Results:\n")
            for status, count in status_counts.items():
                f.write(f"  {status}: {count} places\n")
            
            f.write("\nDetailed Results:\n")
            for result in results:
                f.write(f"\n{result.name} ({result.status})\n")
                if hasattr(result, 'quality_metrics') and result.quality_metrics:
                    f.write(f"  Quality Score: {result.quality_metrics.get_overall_score()}\n")
                if hasattr(result, 'errors') and result.errors:
                    f.write(f"  Errors: {', '.join(result.errors)}\n")
        
        print(f"     ✓ Processing report saved to {report_file}")
        
    except Exception as e:
        print(f"     ❌ Error saving processing results: {e}")


if __name__ == "__main__":
    from datetime import datetime
    exit_code = main()
    sys.exit(exit_code)
