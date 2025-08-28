#!/usr/bin/env python3
"""
Time Out Bangkok Places Scraper
Extracts individual places with titles, images, and descriptions from Time Out Bangkok
"""

import sys
import time
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Добавляем src в Python path
sys.path.insert(0, str(Path('.') / 'src'))

from integration import create_places_pipeline
from cache import CacheConfig


def get_timeout_html(url: str, timeout: int = 15):
    """
    Получает HTML с Time Out Bangkok
    """
    import requests
    from bs4 import BeautifulSoup
    import random
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0"
    }
    
    try:
        session = requests.Session()
        session.headers.update(headers)
        
        # Пауза между запросами
        time.sleep(random.uniform(1, 3))
        
        response = session.get(url, timeout=timeout)
        if response.status_code != 200:
            print(f"HTTP {response.status_code} for {url}")
            return None
        
        return BeautifulSoup(response.text, "html.parser")
        
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_places_from_best_things_page(url: str) -> List[Dict[str, Any]]:
    """
    Извлекает места со страницы "Best Things to Do in Bangkok"
    """
    places = []
    
    try:
        print(f"📄 Fetching: {url}")
        soup = get_timeout_html(url)
        if not soup:
            print(f"  ❌ Failed to get HTML")
            return places
        
        # Ищем все места на странице
        # Каждое место обычно находится в отдельном блоке
        place_blocks = find_place_blocks(soup)
        print(f"  📊 Found {len(place_blocks)} place blocks")
        
        for i, block in enumerate(place_blocks):
            try:
                place = extract_place_from_block(block, i+1)
                if place:
                    places.append(place)
                    print(f"    ✓ Extracted: {place['title'][:40]}...")
                    
            except Exception as e:
                print(f"    ⚠️ Error extracting place {i+1}: {e}")
                continue
        
        print(f"  ✅ Successfully extracted {len(places)} places")
        return places
        
    except Exception as e:
        print(f"  ❌ Error processing page: {e}")
        return places


def find_place_blocks(soup):
    """
    Находит блоки с местами на странице
    """
    place_blocks = []
    
    # Ищем различные структуры, где могут быть места
    
    # 1. Ищем заголовки h2, h3, h4 (обычно это названия мест)
    headings = soup.find_all(['h2', 'h3', 'h4'])
    
    for heading in headings:
        # Пропускаем технические заголовки
        heading_text = heading.get_text(strip=True)
        if any(skip in heading_text.lower() for skip in [
            'the best things to do in bangkok', 'advertising', 'popular on time out',
            'you may also like', 'discover time out', 'about us', 'contact us'
        ]):
            continue
        
        # Если заголовок выглядит как название места
        if len(heading_text) > 5 and len(heading_text) < 100:
            # Ищем ближайший блок с контентом
            block = find_content_block_for_heading(heading)
            if block:
                place_blocks.append(block)
    
    # 2. Ищем блоки с изображениями и описаниями
    images = soup.find_all('img')
    for img in images:
        alt = img.get('alt', '')
        if alt and len(alt) > 10:
            # Ищем блок с этим изображением
            block = find_content_block_for_image(img)
            if block and block not in place_blocks:
                place_blocks.append(block)
    
    # Убираем дубликаты
    unique_blocks = []
    seen_content = set()
    
    for block in place_blocks:
        content_hash = hash(str(block))
        if content_hash not in seen_content:
            unique_blocks.append(block)
            seen_content.add(content_hash)
    
    return unique_blocks


def find_content_block_for_heading(heading):
    """
    Находит блок с контентом для заголовка
    """
    try:
        # Ищем родительский контейнер
        parent = heading.parent
        
        # Ищем изображение рядом
        nearby_image = find_nearby_image(heading)
        
        # Ищем описание
        description = find_nearby_description(heading)
        
        # Создаем блок с контентом
        block = {
            'heading': heading,
            'image': nearby_image,
            'description': description,
            'parent': parent
        }
        
        return block
        
    except Exception:
        return None


def find_content_block_for_image(img):
    """
    Находит блок с контентом для изображения
    """
    try:
        # Ищем родительский контейнер
        parent = img.parent
        
        # Ищем заголовок рядом
        nearby_heading = find_nearby_heading(img)
        
        # Ищем описание
        description = find_nearby_description(img)
        
        # Создаем блок с контентом
        block = {
            'heading': nearby_heading,
            'image': img,
            'description': description,
            'parent': parent
        }
        
        return block
        
    except Exception:
        return None


def find_nearby_image(element, max_distance: int = 5):
    """
    Ищет изображение рядом с элементом
    """
    try:
        # Ищем в родительском элементе
        parent = element.parent
        if parent:
            img = parent.find('img')
            if img:
                return img
            
            # Ищем в соседних элементах
            siblings = parent.find_next_siblings()
            for sibling in siblings[:max_distance]:
                img = sibling.find('img')
                if img:
                    return img
        
        return None
        
    except Exception:
        return None


def find_nearby_heading(element, max_distance: int = 5):
    """
    Ищет заголовок рядом с элементом
    """
    try:
        # Ищем в родительском элементе
        parent = element.parent
        if parent:
            heading = parent.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if heading:
                return heading
            
            # Ищем в соседних элементах
            siblings = parent.find_next_siblings()
            for sibling in siblings[:max_distance]:
                heading = sibling.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if heading:
                    return heading
        
        return None
        
    except Exception:
        return None


def find_nearby_description(element, max_distance: int = 5):
    """
    Ищет описание рядом с элементом
    """
    try:
        # Ищем в родительском элементе
        parent = element.parent
        if parent:
            # Ищем параграфы с описанием
            paragraphs = parent.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    return p
            
            # Ищем в соседних элементах
            siblings = parent.find_next_siblings()
            for sibling in siblings[:max_distance]:
                paragraphs = sibling.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        return p
        
        return None
        
    except Exception:
        return None


def extract_place_from_block(block, place_num: int) -> Optional[Dict[str, Any]]:
    """
    Извлекает информацию о месте из блока
    """
    try:
        # Заголовок
        title = ""
        if block.get('heading'):
            title = block['heading'].get_text(strip=True)
        elif block.get('image'):
            alt = block['image'].get('alt', '')
            if alt and len(alt) > 5:
                title = alt
        
        if not title or len(title) < 5:
            return None
        
        # Изображение
        image_url = None
        if block.get('image'):
            src = block['image'].get('src', '')
            if src and src.startswith('http'):
                image_url = src
        
        # Описание
        description = ""
        if block.get('description'):
            desc_text = block['description'].get_text(strip=True)
            if desc_text and len(desc_text) > 20:
                description = desc_text[:300]  # Ограничиваем длину
        
        # Если нет описания, используем alt текст изображения
        if not description and block.get('image'):
            alt = block['image'].get('alt', '')
            if alt and len(alt) > 10:
                description = alt
        
        # Определяем флаги на основе заголовка и описания
        flags = determine_flags_from_content(title, description)
        
        # Создаем место
        place = {
            'title': title,
            'image': image_url,
            'description': description,
            'flags': flags,
            'source': 'timeout.com',
            'city': 'Bangkok',
            'place_number': place_num
        }
        
        return place
        
    except Exception as e:
        print(f"      ⚠️ Error extracting place: {e}")
        return None


def determine_flags_from_content(title: str, description: str) -> List[str]:
    """
    Определяет флаги на основе заголовка и описания
    """
    flags = []
    
    # Объединяем текст для анализа
    content = (title + " " + description).lower()
    
    # Определяем категории на основе ключевых слов
    if any(word in content for word in ['restaurant', 'food', 'dining', 'eat', 'cuisine']):
        flags.extend(['food_dining', 'restaurants'])
    elif any(word in content for word in ['bar', 'pub', 'nightlife', 'club', 'drink']):
        flags.extend(['nightlife', 'bars'])
    elif any(word in content for word in ['market', 'shopping', 'mall', 'shop']):
        flags.extend(['shopping', 'markets'])
    elif any(word in content for word in ['museum', 'gallery', 'art', 'exhibition']):
        flags.extend(['culture', 'art', 'museums'])
    elif any(word in content for word in ['park', 'garden', 'nature', 'forest']):
        flags.extend(['nature', 'parks', 'outdoors'])
    elif any(word in content for word in ['spa', 'wellness', 'yoga', 'fitness']):
        flags.extend(['wellness', 'health'])
    elif any(word in content for word in ['hotel', 'accommodation', 'resort']):
        flags.extend(['accommodation', 'hotels'])
    elif any(word in content for word in ['theater', 'cinema', 'concert', 'show', 'performance']):
        flags.extend(['entertainment', 'culture'])
    elif any(word in content for word in ['temple', 'wat', 'religious', 'buddhist']):
        flags.extend(['culture', 'religion', 'temples'])
    elif any(word in content for word in ['street', 'alley', 'soi', 'neighborhood']):
        flags.extend(['local', 'neighborhoods'])
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
    places = extract_places_from_best_things_page(main_url)
    
    if not places:
        print("❌ No places collected")
        return []
    
    print(f"📊 Collection Summary:")
    print(f"   Total places found: {len(places)}")
    
    return places


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
        raw_file = results_dir / f'timeout_bangkok_places_raw_{timestamp}.json'
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(places, f, indent=2, ensure_ascii=False)
        print(f"     ✓ Raw data saved to {raw_file}")
        
        # Сохраняем данные для пайплайна
        pipeline_file = results_dir / f'timeout_bangkok_places_pipeline_{timestamp}.json'
        with open(pipeline_file, 'w', encoding='utf-8') as f:
            json.dump(pipeline_places, f, indent=2, ensure_ascii=False)
        print(f"     ✓ Pipeline data saved to {pipeline_file}")
        
        # Сохраняем отчет
        report_file = results_dir / f'timeout_bangkok_places_report_{timestamp}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("Time Out Bangkok Places Collection Report\n")
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
