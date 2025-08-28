#!/usr/bin/env python3
"""
Updated Time Out Bangkok Scraper
Uses the correct selectors based on current site structure
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


def extract_places_from_page(url: str, category: str = "general") -> List[Dict[str, Any]]:
    """
    Извлекает места со страницы Time Out Bangkok
    """
    places = []
    
    try:
        print(f"     📄 Fetching: {url}")
        soup = get_timeout_html(url)
        if not soup:
            print(f"       ❌ Failed to get HTML")
            return places
        
        # Ищем все статьи с правильными селекторами
        articles = soup.find_all('article', class_='_article_a9wsr_1')
        print(f"       📊 Found {len(articles)} articles")
        
        for article in articles:
            try:
                place = extract_place_from_article(article, category)
                if place:
                    places.append(place)
                    
            except Exception as e:
                print(f"       ⚠️ Error extracting place from article: {e}")
                continue
        
        print(f"       ✅ Extracted {len(places)} places")
        return places
        
    except Exception as e:
        print(f"       ❌ Error processing page: {e}")
        return places


def extract_place_from_article(article, category: str) -> Optional[Dict[str, Any]]:
    """
    Извлекает информацию о месте из статьи
    """
    try:
        # Заголовок - ищем h3 с правильным классом
        title_el = article.find('h3', class_='_h3_c6c0h_1')
        if not title_el:
            # Фолбэк: любой h3
            title_el = article.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        if not title_el:
            return None
        
        title = title_el.get_text(strip=True)
        if not title or len(title) < 5:
            return None
        
        # Ссылка - ищем с правильным классом
        link_el = article.find('a', class_='_titleLinkContainer_a9wsr_48')
        if not link_el:
            # Фолбэк: любая ссылка
            link_el = article.find('a')
        
        if not link_el:
            return None
        
        href = link_el.get('href', '')
        if not href:
            return None
        
        # Полный URL
        if href.startswith('/'):
            url = f"https://www.timeout.com{href}"
        elif href.startswith('http'):
            url = href
        else:
            return None
        
        # Изображение - ищем с правильными классами
        image_url = None
        img_el = article.find('img', class_='_image_a9wsr_26')
        if not img_el:
            # Фолбэк: любое изображение
            img_el = article.find('img')
        
        if img_el:
            src = img_el.get('src', '')
            if src and src.startswith('http'):
                image_url = src
        
        # Описание (из alt текста изображения)
        description = None
        if img_el:
            alt = img_el.get('alt', '')
            if alt and len(alt) > 10:
                description = alt
        
        # Определяем флаги на основе категории и URL
        flags = determine_flags_from_url(url, category)
        
        # Создаем место
        place = {
            'title': title,
            'url': url,
            'image': image_url,
            'description': description,
            'category': category,
            'flags': flags,
            'source': 'timeout.com',
            'city': 'Bangkok'
        }
        
        return place
        
    except Exception as e:
        print(f"         ⚠️ Error extracting place: {e}")
        return None


def determine_flags_from_url(url: str, category: str) -> List[str]:
    """
    Определяет флаги на основе URL и категории
    """
    flags = []
    
    # Анализируем URL для определения типа места
    url_lower = url.lower()
    
    if any(word in url_lower for word in ['restaurant', 'food', 'dining']):
        flags.extend(['food_dining', 'restaurants'])
    elif any(word in url_lower for word in ['bar', 'pub', 'nightlife', 'club']):
        flags.extend(['nightlife', 'bars'])
    elif any(word in url_lower for word in ['market', 'shopping', 'mall']):
        flags.extend(['shopping', 'markets'])
    elif any(word in url_lower for word in ['museum', 'gallery', 'art', 'exhibition']):
        flags.extend(['culture', 'art', 'museums'])
    elif any(word in url_lower for word in ['park', 'garden', 'nature']):
        flags.extend(['nature', 'parks', 'outdoors'])
    elif any(word in url_lower for word in ['spa', 'wellness', 'yoga', 'fitness']):
        flags.extend(['wellness', 'health'])
    elif any(word in url_lower for word in ['hotel', 'accommodation', 'resort']):
        flags.extend(['accommodation', 'hotels'])
    elif any(word in url_lower for word in ['theater', 'cinema', 'concert', 'show']):
        flags.extend(['entertainment', 'culture'])
    else:
        # Базовые флаги на основе категории
        if category in ['food', 'restaurants']:
            flags.extend(['food_dining', 'restaurants'])
        elif category in ['bars', 'nightlife']:
            flags.extend(['nightlife', 'bars'])
        elif category in ['attractions', 'things-to-do']:
            flags.extend(['attractions', 'things_to_do'])
        elif category in ['shopping', 'markets']:
            flags.extend(['shopping', 'markets'])
        else:
            flags.append('attractions')
    
    return flags


def collect_timeout_bangkok_places() -> List[Dict[str, Any]]:
    """
    Собирает места со всех доступных страниц Time Out Bangkok
    """
    print("🚀 Starting Time Out Bangkok Places Collection...")
    print("=" * 60)
    
    all_places = []
    
    # Основные страницы для сбора
    collection_urls = [
        {
            'url': 'https://www.timeout.com/bangkok',
            'category': 'general'
        },
        {
            'url': 'https://www.timeout.com/bangkok/things-to-do',
            'category': 'attractions'
        }
    ]
    
    # Попробуем другие возможные URL
    additional_urls = [
        'https://www.timeout.com/bangkok/food-drink',
        'https://www.timeout.com/bangkok/music-nightlife',
        'https://www.timeout.com/bangkok/shopping',
        'https://www.timeout.com/bangkok/events'
    ]
    
    # Собираем с основных страниц
    for collection in collection_urls:
        print(f"📡 Collecting from: {collection['url']}")
        places = extract_places_from_page(collection['url'], collection['category'])
        all_places.extend(places)
        
        # Пауза между страницами
        time.sleep(2)
    
    # Пробуем дополнительные URL
    for url in additional_urls:
        print(f"📡 Trying additional URL: {url}")
        try:
            places = extract_places_from_page(url, 'general')
            if places:
                all_places.extend(places)
                print(f"       ✅ Got {len(places)} places from {url}")
            else:
                print(f"       ⚠️ No places from {url}")
        except Exception as e:
            print(f"       ❌ Error with {url}: {e}")
        
        time.sleep(2)
    
    # Убираем дубликаты по URL
    unique_places = []
    seen_urls = set()
    
    for place in all_places:
        if place['url'] not in seen_urls:
            unique_places.append(place)
            seen_urls.add(place['url'])
    
    print(f"📊 Collection Summary:")
    print(f"   Total places found: {len(all_places)}")
    print(f"   Unique places: {len(unique_places)}")
    print(f"   Duplicates removed: {len(all_places) - len(unique_places)}")
    
    return unique_places


def convert_to_pipeline_format(places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Конвертирует места Time Out в формат для пайплайна
    """
    pipeline_places = []
    
    for i, place in enumerate(places):
        try:
            # Создаем уникальный ID
            place_id = f"timeout_{i+1}_{int(time.time())}"
            
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
                'description': place.get('description', ''),
                'address': 'Bangkok, Thailand',  # Time Out не предоставляет точный адрес
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
                'quality_score': 0.85,  # Базовый score для Time Out
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
        raw_file = results_dir / f'timeout_bangkok_raw_{timestamp}.json'
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(places, f, indent=2, ensure_ascii=False)
        print(f"     ✓ Raw data saved to {raw_file}")
        
        # Сохраняем данные для пайплайна
        pipeline_file = results_dir / f'timeout_bangkok_pipeline_{timestamp}.json'
        with open(pipeline_file, 'w', encoding='utf-8') as f:
            json.dump(pipeline_places, f, indent=2, ensure_ascii=False)
        print(f"     ✓ Pipeline data saved to {pipeline_file}")
        
        # Сохраняем отчет
        report_file = results_dir / f'timeout_bangkok_report_{timestamp}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("Time Out Bangkok Collection Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Collection Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Places: {len(places)}\n")
            f.write(f"Pipeline Ready: {len(pipeline_places)}\n\n")
            
            f.write("Collected Places:\n")
            for i, place in enumerate(places, 1):
                f.write(f"\n{i}. {place.get('title', 'Unknown')}\n")
                f.write(f"   URL: {place.get('url', 'No URL')}\n")
                f.write(f"   Category: {place.get('category', 'Unknown')}\n")
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
