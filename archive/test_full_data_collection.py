#!/usr/bin/env python3
"""
Комплексный тест сбора событий по всем категориям с полным набором данных
Проверяет количество и качество собираемых данных
"""

import sys
from pathlib import Path
import time
import json
from collections import defaultdict

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from core.live_events import fetch_from_sources, get_available_sources

# Загружаем sources из JSON файла
def load_sources():
    with open('data/sources.json', 'r', encoding='utf-8') as f:
        return json.load(f)

sources = load_sources()

def analyze_event_quality(event):
    """Анализирует качество отдельного события"""
    quality_score = 0
    missing_fields = []
    
    # Проверяем обязательные поля
    if event.get('title'):
        quality_score += 20
    else:
        missing_fields.append('title')
    
    if event.get('date'):
        quality_score += 20
    else:
        missing_fields.append('date')
    
    if event.get('url'):
        quality_score += 15
    else:
        missing_fields.append('url')
    
    # Проверяем дополнительные поля
    if event.get('image'):
        quality_score += 15
    else:
        missing_fields.append('image')
    
    if event.get('venue'):
        quality_score += 10
    else:
        missing_fields.append('venue')
    
    if event.get('desc'):
        quality_score += 10
    else:
        missing_fields.append('desc')
    
    if event.get('tags'):
        quality_score += 10
    else:
        missing_fields.append('tags')
    
    return quality_score, missing_fields

def test_category_data_collection(category_id, source_ids):
    """Тестирует сбор данных для конкретной категории"""
    print(f"\n🎯 Тестируем категорию: {category_id}")
    print(f"📡 Источники: {', '.join(source_ids)}")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # Собираем события из всех источников категории
        events = fetch_from_sources(source_ids, category_id)
        elapsed = time.time() - start_time
        
        print(f"✅ Получено событий: {len(events)} за {elapsed:.2f}с")
        
        if not events:
            print("❌ События не найдены")
            return {
                'category': category_id,
                'total_events': 0,
                'quality_stats': {},
                'elapsed_time': elapsed,
                'sources': source_ids
            }
        
        # Анализируем качество каждого события
        quality_scores = []
        missing_fields_count = defaultdict(int)
        tags_distribution = defaultdict(int)
        venues_distribution = defaultdict(int)
        
        for event in events:
            quality_score, missing_fields = analyze_event_quality(event)
            quality_scores.append(quality_score)
            
            # Подсчитываем недостающие поля
            for field in missing_fields:
                missing_fields_count[field] += 1
            
            # Анализируем теги
            for tag in event.get('tags', []):
                tags_distribution[tag] += 1
            
            # Анализируем места проведения
            if event.get('venue'):
                venues_distribution[event['venue']] += 1
        
        # Статистика качества
        avg_quality = sum(quality_scores) / len(quality_scores)
        min_quality = min(quality_scores)
        max_quality = max(quality_scores)
        
        # Показываем примеры событий
        print(f"\n📊 КАЧЕСТВО ДАННЫХ:")
        print(f"  Средний балл: {avg_quality:.1f}/100")
        print(f"  Минимальный: {min_quality}/100")
        print(f"  Максимальный: {max_quality}/100")
        
        print(f"\n❌ НЕДОСТАЮЩИЕ ПОЛЯ:")
        for field, count in sorted(missing_fields_count.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(events)) * 100
            print(f"  {field}: {count} ({percentage:.1f}%)")
        
        print(f"\n🏷 ТЕГИ (топ-10):")
        for tag, count in sorted(tags_distribution.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {tag}: {count}")
        
        print(f"\n📍 МЕСТА ПРОВЕДЕНИЯ (топ-10):")
        for venue, count in sorted(venues_distribution.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {venue}: {count}")
        
        # Показываем лучшие и худшие события
        best_events = sorted(events, key=lambda x: analyze_event_quality(x)[0], reverse=True)[:3]
        worst_events = sorted(events, key=lambda x: analyze_event_quality(x)[0])[:3]
        
        print(f"\n🏆 ЛУЧШИЕ СОБЫТИЯ:")
        for i, event in enumerate(best_events):
            quality_score, _ = analyze_event_quality(event)
            print(f"  {i+1}. {event.get('title', 'No title')} - {quality_score}/100")
            print(f"     Дата: {event.get('date', 'No date')}")
            print(f"     URL: {event.get('url', 'No URL')}")
            print(f"     Image: {'✅' if event.get('image') else '❌'}")
            print(f"     Venue: {'✅' if event.get('venue') else '❌'}")
            print(f"     Tags: {event.get('tags', [])}")
        
        print(f"\n⚠️ СОБЫТИЯ С НИЗКИМ КАЧЕСТВОМ:")
        for i, event in enumerate(worst_events):
            quality_score, missing = analyze_event_quality(event)
            print(f"  {i+1}. {event.get('title', 'No title')} - {quality_score}/100")
            print(f"     Недостает: {', '.join(missing)}")
        
        return {
            'category': category_id,
            'total_events': len(events),
            'quality_stats': {
                'average': avg_quality,
                'min': min_quality,
                'max': max_quality
            },
            'missing_fields': dict(missing_fields_count),
            'tags_distribution': dict(tags_distribution),
            'venues_distribution': dict(venues_distribution),
            'elapsed_time': elapsed,
            'sources': source_ids
        }
        
    except Exception as e:
        print(f"❌ Ошибка при сборе данных: {e}")
        return {
            'category': category_id,
            'total_events': 0,
            'error': str(e),
            'sources': source_ids
        }

def test_all_categories():
    """Тестирует сбор данных по всем категориям"""
    print("🚀 КОМПЛЕКСНЫЙ ТЕСТ СБОРА СОБЫТИЙ")
    print("=" * 80)
    
    results = {}
    total_events = 0
    total_time = 0
    
    # Тестируем каждую категорию
    for category_id, source_ids in sources.items():
        result = test_category_data_collection(category_id, source_ids)
        results[category_id] = result
        
        if 'total_events' in result:
            total_events += result['total_events']
            total_time += result.get('elapsed_time', 0)
    
    # Итоговая статистика
    print("\n" + "=" * 80)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 80)
    
    print(f"\n🎯 ВСЕГО СОБРАНО СОБЫТИЙ: {total_events}")
    print(f"⏱ ОБЩЕЕ ВРЕМЯ СБОРА: {total_time:.2f}с")
    
    print(f"\n📈 СТАТИСТИКА ПО КАТЕГОРИЯМ:")
    for category_id, result in results.items():
        if 'total_events' in result and result['total_events'] > 0:
            quality = result.get('quality_stats', {}).get('average', 0)
            print(f"  {category_id}: {result['total_events']} событий, качество: {quality:.1f}/100")
        else:
            print(f"  {category_id}: 0 событий")
    
    # Анализ качества данных
    print(f"\n🔍 АНАЛИЗ КАЧЕСТВА ДАННЫХ:")
    
    # Собираем статистику по недостающим полям
    all_missing_fields = defaultdict(int)
    all_tags = defaultdict(int)
    all_venues = defaultdict(int)
    
    for result in results.values():
        if 'missing_fields' in result:
            for field, count in result['missing_fields'].items():
                all_missing_fields[field] += count
        
        if 'tags_distribution' in result:
            for tag, count in result['tags_distribution'].items():
                all_tags[tag] += count
        
        if 'venues_distribution' in result:
            for venue, count in result['venues_distribution'].items():
                all_venues[venue] += count
    
    print(f"\n❌ ОБЩИЕ НЕДОСТАЮЩИЕ ПОЛЯ:")
    for field, count in sorted(all_missing_fields.items(), key=lambda x: x[1], reverse=True):
        print(f"  {field}: {count}")
    
    print(f"\n🏷 ОБЩИЕ ТЕГИ (топ-15):")
    for tag, count in sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"  {tag}: {count}")
    
    print(f"\n📍 ОБЩИЕ МЕСТА ПРОВЕДЕНИЯ (топ-15):")
    for venue, count in sorted(all_venues.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"  {venue}: {count}")
    
    # Сохраняем результаты в файл
    output_file = "test_results_full_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_events': total_events,
                'total_time': total_time,
                'categories_tested': len(results)
            },
            'results': results,
            'global_stats': {
                'missing_fields': dict(all_missing_fields),
                'tags_distribution': dict(all_tags),
                'venues_distribution': dict(all_venues)
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Результаты сохранены в {output_file}")
    
    return results

def test_specific_sources():
    """Тестирует отдельные источники для проверки их работы"""
    print("\n🔍 ТЕСТИРОВАНИЕ ОТДЕЛЬНЫХ ИСТОЧНИКОВ")
    print("=" * 60)
    
    available_sources = get_available_sources()
    print(f"Доступные источники: {', '.join(available_sources)}")
    
    # Тестируем каждый источник отдельно
    for source_id in available_sources:
        print(f"\n🧪 Тестируем источник: {source_id}")
        try:
            start_time = time.time()
            events = fetch_from_sources([source_id])
            elapsed = time.time() - start_time
            
            print(f"  ✅ Событий: {len(events)} за {elapsed:.2f}с")
            
            if events:
                # Анализируем качество
                quality_scores = []
                for event in events:
                    quality_score, _ = analyze_event_quality(event)
                    quality_scores.append(quality_score)
                
                avg_quality = sum(quality_scores) / len(quality_scores)
                print(f"  📊 Среднее качество: {avg_quality:.1f}/100")
                
                # Показываем пример
                best_event = max(events, key=lambda x: analyze_event_quality(x)[0])
                print(f"  📅 Пример: {best_event.get('title', 'No title')}")
                print(f"     Дата: {best_event.get('date', 'No date')}")
                print(f"     Image: {'✅' if best_event.get('image') else '❌'}")
                print(f"     Venue: {'✅' if best_event.get('venue') else '❌'}")
            
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")

if __name__ == "__main__":
    # Основной тест по категориям
    results = test_all_categories()
    
    # Дополнительный тест отдельных источников
    test_specific_sources()
    
    print(f"\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print(f"📊 Проверено категорий: {len(results)}")
    print(f"📈 Общее количество событий: {sum(r.get('total_events', 0) for r in results.values())}")
