#!/usr/bin/env python3
"""
Simple Time Out Bangkok Places Scraper
Uses specific selectors to find places on the page
"""

import sys
import time
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Добавляем src и tools в Python path
sys.path.insert(0, str(Path('.') / 'src'))
sys.path.insert(0, str(Path('.') / 'tools'))

from integration import create_places_pipeline
from cache import CacheConfig
from fetchers.base import get_html


def extract_places_simple(soup):
    """
    Простое извлечение мест по конкретным селекторам
    """
    places = []
    
    try:
        print("  🔍 Looking for places using simple selectors...")
        
        # 1. Ищем все изображения с alt текстом
        images = soup.find_all('img')
        print(f"    Found {len(images)} images")
        
        for img in images:
            alt = img.get('alt', '')
            src = img.get('src', '')
            
            # Пропускаем технические изображения
            if any(skip in alt.lower() for skip in [
                'loading', 'advertising', 'logo', 'icon', 'button', 'animation'
            ]):
                continue
            
            # Пропускаем изображения авторов
            if any(skip in alt.lower() for skip in [
                'napatsorn', 'kaweewat', 'can srisawat', 'prowd'
            ]):
                continue
            
            # Если у изображения есть alt текст и src
            if alt and len(alt) > 5 and src and src.startswith('http'):
                print(f"      Image: {alt[:40]}...")
                
                # Ищем описание рядом с изображением
                description = find_description_near_image(img)
                
                # Определяем флаги
                flags = determine_flags_from_text(alt)
                
                place = {
                    'title': alt,
                    'image': src,
                    'description': description,
                    'flags': flags,
                    'source': 'timeout.com',
                    'city': 'Bangkok'
                }
                
                places.append(place)
        
        # 2. Ищем заголовки, которые могут быть названиями мест
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        print(f"    Found {len(headings)} headings")
        
        for heading in headings:
            text = heading.get_text(strip=True)
            
            # Пропускаем технические заголовки
            if any(skip in text.lower() for skip in [
                'the best things to do in bangkok', 'advertising', 'popular on time out',
                'you may also like', 'discover time out', 'about us', 'contact us',
                'subscribe', 'newsletter', 'search', 'explore cities', 'go to the content',
                'go to the footer', 'no thanks', 'awesome', 'thanks for subscribing'
            ]):
                continue
            
            # Если заголовок выглядит как название места
            if len(text) > 5 and len(text) < 100:
                print(f"      Heading: {text[:40]}...")
                
                # Ищем изображение рядом
                nearby_image = find_image_near_heading(heading)
                
                # Ищем описание
                description = find_description_near_heading(heading)
                
                # Определяем флаги
                flags = determine_flags_from_text(text)
                
                place = {
                    'title': text,
                    'image': nearby_image,
                    'description': description,
                    'flags': flags,
                    'source': 'timeout.com',
                    'city': 'Bangkok'
                }
                
                # Проверяем, что это место еще не добавлено
                if not any(p['title'] == text for p in places):
                    places.append(place)
        
        print(f"    Total unique places found: {len(places)}")
        return places
        
    except Exception as e:
        print(f"    ❌ Error in simple extraction: {e}")
        return []


def find_description_near_image(img):
    """
    Ищет описание рядом с изображением
    """
    try:
        # Ищем в родительском элементе
        parent = img.parent
        if parent:
            # Ищем параграфы
            paragraphs = parent.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    return text[:300]
            
            # Ищем в соседних элементах
            siblings = parent.find_next_siblings()
            for sibling in siblings[:3]:
                paragraphs = sibling.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        return text[:300]
        
        return ""
        
    except Exception:
        return ""


def find_image_near_heading(heading):
    """
    Ищет изображение рядом с заголовком
    """
    try:
        # Ищем в родительском элементе
        parent = heading.parent
        if parent:
            img = parent.find('img')
            if img:
                src = img.get('src', '')
                if src and src.startswith('http'):
                    return src
            
            # Ищем в соседних элементах
            siblings = parent.find_next_siblings()
            for sibling in siblings[:3]:
                img = sibling.find('img')
                if img:
                    src = img.get('src', '')
                    if src and src.startswith('http'):
                        return src
        
        return ""
        
    except Exception:
        return ""


def find_description_near_heading(heading):
    """
    Ищет описание рядом с заголовком
    """
    try:
        # Ищем в родительском элементе
        parent = heading.parent
        if parent:
            # Ищем параграфы
            paragraphs = parent.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    return text[:300]
            
            # Ищем в соседних элементах
            siblings = parent.find_next_siblings()
            for sibling in siblings[:3]:
                paragraphs = sibling.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        return text[:300]
        
        return ""
        
    except Exception:
        return ""


def determine_flags_from_text(text: str) -> List[str]:
    """
    Определяет флаги на основе текста
    """
    flags = []
    text_lower = text.lower()
    
    # Определяем категории на основе ключевых слов
    if any(word in text_lower for word in ['restaurant', 'food', 'dining', 'eat', 'cuisine', 'cook']):
        flags.extend(['food_dining', 'restaurants'])
    elif any(word in text_lower for word in ['bar', 'pub', 'nightlife', 'club', 'drink', 'cocktail']):
        flags.extend(['nightlife', 'bars'])
    elif any(word in text_lower for word in ['market', 'shopping', 'mall', 'shop', 'buy']):
        flags.extend(['shopping', 'markets'])
    elif any(word in text_lower for word in ['museum', 'gallery', 'art', 'exhibition', 'exhibit']):
        flags.extend(['culture', 'art', 'museums'])
    elif any(word in text_lower for word in ['park', 'garden', 'nature', 'forest', 'outdoor']):
        flags.extend(['nature', 'parks', 'outdoors'])
    elif any(word in text_lower for word in ['spa', 'wellness', 'yoga', 'fitness', 'health']):
        flags.extend(['wellness', 'health'])
    elif any(word in text_lower for word in ['hotel', 'accommodation', 'resort', 'stay']):
        flags.extend(['accommodation', 'hotels'])
    elif any(word in text_lower for word in ['theater', 'cinema', 'concert', 'show', 'performance', 'dance']):
        flags.extend(['entertainment', 'culture'])
    elif any(word in text_lower for word in ['temple', 'wat', 'religious', 'buddhist', 'shrine']):
        flags.extend(['culture', 'religion', 'temples'])
    elif any(word in text_lower for word in ['street', 'alley', 'soi', 'neighborhood', 'area']):
        flags.extend(['local', 'neighborhoods'])
    elif any(word in text_lower for word in ['planetarium', 'science', 'technology']):
        flags.extend(['education', 'science'])
    elif any(word in text_lower for word in ['farm', 'snake', 'animal', 'zoo']):
        flags.extend(['nature', 'animals'])
    elif any(word in text_lower for word in ['bank', 'learning', 'centre', 'center']):
        flags.extend(['education', 'culture'])
    elif any(word in text_lower for word in ['drag', 'lgbtq', 'culture']):
        flags.extend(['entertainment', 'culture'])
    elif any(word in text_lower for word in ['lizard', 'monitor', 'park']):
        flags.extend(['nature', 'parks'])
    elif any(word in text_lower for word in ['street art', 'graffiti', 'mural']):
        flags.extend(['art', 'culture'])
    elif any(word in text_lower for word in ['traditional', 'outfit', 'dress', 'costume']):
        flags.extend(['culture', 'fashion'])
    elif any(word in text_lower for word in ['hop', 'bar hopping']):
        flags.extend(['nightlife', 'bars'])
    else:
        flags.append('attractions')
    
    return flags


def collect_timeout_bangkok_places() -> List[Dict[str, Any]]:
    """
    Собирает места со страницы "Best Things to Do in Bangkok"
    """
    print("🚀 Starting Time Out Bangkok Places Collection...")
    print("=" * 60)
    
    # Основная страница с местами
    main_url = "https://www.timeout.com/bangkok/things-to-do/best-things-to-do-in-bangkok"
    
    print(f"📡 Collecting from: {main_url}")
    
    try:
        soup = get_html(main_url)
        if not soup:
            print("  ❌ Failed to get HTML")
            return []
        
        # Извлекаем места
        places = extract_places_simple(soup)
        
        if not places:
            print("  ❌ No places found")
            return []
        
        print(f"📊 Collection Summary:")
        print(f"   Total places found: {len(places)}")
        
        return places
        
    except Exception as e:
        print(f"  ❌ Error in collection: {e}")
        return []


def convert_to_pipeline_format(places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Конвертирует места Time Out в формат для пайплайна
    """
    pipeline_places = []
    
    for i, place in enumerate(places):
        try:
            # Создаем уникальный ID
            place_id = f"timeout_place_{i+1}_{int(time.time())}"
            
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
                'url': '',  # Time Out не предоставляет прямые ссылки на места
                'description': place.get('description', ''),
                'address': 'Bangkok, Thailand',
                'geo_lat': None,
                'geo_lng': None,
                'tags': [],
                'flags': place.get('flags', ['attractions']),
                'phone': None,
                'email': None,
                'website': None,
                'hours': None,
                'price_level': None,
                'rating': None,
                'photos': photos,
                'image_url': image_url,
                'quality_score': 0.85,
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            }
            
            pipeline_places.append(pipeline_place)
            
        except Exception as e:
            print(f"     ⚠️ Error converting place {i}: {e}")
            continue
    
    print(f"     ✓ Converted {len(pipeline_places)} places to pipeline format")
    return pipeline_places


def main():
    """Main function to collect and process Time Out Bangkok places."""
    try:
        # Сбор мест
        places = collect_timeout_bangkok_places()
        
        if not places:
            print("❌ No places collected")
            return 1
        
        # Конвертация в формат пайплайна
        print("\n🔄 Converting places to pipeline format...")
        pipeline_places = convert_to_pipeline_format(places)
        
        # Сохранение результатов
        print("\n💾 Saving collected places...")
        save_collected_places(places, pipeline_places)
        
        print("\n✅ Time Out Bangkok collection completed!")
        print(f"📊 Total places collected: {len(places)}")
        print(f"🔄 Places ready for pipeline: {len(pipeline_places)}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error in collection: {e}")
        import traceback
        traceback.print_exc()
        return 1


def save_collected_places(places: List[Dict], pipeline_places: List[Dict]):
    """Save collected places to files."""
    try:
        # Создаем директорию для результатов
        results_dir = Path('results')
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Сохраняем исходные данные
        raw_file = results_dir / f'timeout_bangkok_simple_raw_{timestamp}.json'
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(places, f, indent=2, ensure_ascii=False)
        print(f"     ✓ Raw data saved to {raw_file}")
        
        # Сохраняем данные для пайплайна
        pipeline_file = results_dir / f'timeout_bangkok_simple_pipeline_{timestamp}.json'
        with open(pipeline_file, 'w', encoding='utf-8') as f:
            json.dump(pipeline_places, f, indent=2, ensure_ascii=False)
        print(f"     ✓ Pipeline data saved to {pipeline_file}")
        
        # Сохраняем отчет
        report_file = results_dir / f'timeout_bangkok_simple_report_{timestamp}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("Time Out Bangkok Simple Places Collection Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Collection Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Places: {len(places)}\n")
            f.write(f"Pipeline Ready: {len(pipeline_places)}\n\n")
            
            f.write("Collected Places:\n")
            for i, place in enumerate(places, 1):
                f.write(f"\n{i}. {place.get('title', 'Unknown')}\n")
                f.write(f"   Flags: {', '.join(place.get('flags', []))}\n")
                if place.get('image'):
                    f.write(f"   Image: Yes\n")
                if place.get('description'):
                    f.write(f"   Description: {place.get('description', '')[:100]}...\n")
        
        print(f"     ✓ Report saved to {report_file}")
        
    except Exception as e:
        print(f"     ❌ Error saving results: {e}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
