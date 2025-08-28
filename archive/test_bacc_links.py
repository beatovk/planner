#!/usr/bin/env python3
"""
Тест для анализа всех ссылок на странице Bangkok Art City
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from tools.fetchers.base import get_html
from urllib.parse import urljoin

def test_bacc_links():
    print("🧪 Анализ ссылок Bangkok Art City...")
    
    ROOT = "https://www.bangkokartcity.org"
    LIST_URL = urljoin(ROOT, "/discover/exhibitions")
    
    print(f"🌐 Проверяем: {LIST_URL}")
    
    soup = get_html(LIST_URL)
    if not soup:
        print("❌ Не удалось получить страницу")
        return
    
    # Ищем все ссылки
    all_links = soup.find_all("a", href=True)
    print(f"📋 Всего ссылок: {len(all_links)}")
    
    # Анализируем ссылки
    exhibitions_links = []
    other_links = []
    
    for link in all_links:
        href = link.get("href", "")
        text = link.get_text(strip=True)
        
        # Ищем ссылки, которые могут вести на выставки
        if any(keyword in href.lower() for keyword in ["exhibition", "show", "art", "gallery"]):
            exhibitions_links.append((href, text))
        elif any(keyword in text.lower() for keyword in ["exhibition", "show", "art", "gallery", "display"]):
            exhibitions_links.append((href, text))
        else:
            other_links.append((href, text))
    
    print(f"\n🎨 Потенциальные ссылки на выставки: {len(exhibitions_links)}")
    for href, text in exhibitions_links[:10]:
        print(f"  {href} - {text}")
    
    print(f"\n🔗 Другие ссылки (первые 10): {len(other_links)}")
    for href, text in other_links[:10]:
        print(f"  {href} - {text}")
    
    # Попробуем найти контент по-другому
    print(f"\n🔍 Поиск контента другими способами:")
    
    # Ищем заголовки
    headers = soup.find_all(["h1", "h2", "h3", "h4"])
    print(f"📄 Заголовки: {len(headers)}")
    for header in headers[:5]:
        text = header.get_text(strip=True)
        if text:
            print(f"  {header.name}: {text}")
    
    # Ищем параграфы с текстом
    paragraphs = soup.find_all("p")
    print(f"📝 Параграфы: {len(paragraphs)}")
    for p in paragraphs[:3]:
        text = p.get_text(strip=True)
        if text and len(text) > 20:
            print(f"  {text[:100]}...")

if __name__ == "__main__":
    test_bacc_links()
