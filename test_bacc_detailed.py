#!/usr/bin/env python3
"""
Детальный тест для Bangkok Art City фетчера
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from tools.fetchers.base import get_html
from urllib.parse import urljoin

def test_bacc_detailed():
    print("🧪 Детальный тест Bangkok Art City...")
    
    ROOT = "https://www.bangkokartcity.org"
    LIST_URL = urljoin(ROOT, "/discover/exhibitions")
    
    print(f"🌐 Проверяем: {LIST_URL}")
    
    # Шаг 1: Получаем главную страницу выставок
    soup = get_html(LIST_URL)
    if not soup:
        print("❌ Не удалось получить страницу выставок")
        return
    
    print("✅ Страница выставок получена")
    
    # Шаг 2: Ищем ссылки на выставки
    links = soup.select("a[href*='/exhibitions/'], a[href*='/discover/']")
    print(f"🔗 Найдено ссылок: {len(links)}")
    
    if not links:
        print("❌ Ссылки на выставки не найдены")
        # Попробуем найти любые ссылки
        all_links = soup.find_all("a", href=True)
        print(f"📋 Всего ссылок на странице: {len(all_links)}")
        for i, link in enumerate(all_links[:5]):
            href = link.get("href", "")
            text = link.get_text(strip=True)[:50]
            print(f"  {i+1}. {href} - {text}")
        return
    
    # Шаг 3: Проверяем первые несколько ссылок
    print(f"\n🔍 Проверяем первые {min(3, len(links))} ссылки:")
    
    for i, link in enumerate(links[:3]):
        href = link.get("href", "")
        text = link.get_text(strip=True)
        print(f"\n  {i+1}. {text}")
        print(f"     Ссылка: {href}")
        
        # Получаем полный URL
        url = href if href.startswith("http") else urljoin(ROOT, href)
        print(f"     Полный URL: {url}")
        
        # Получаем детальную страницу
        detail = get_html(url)
        if not detail:
            print("     ❌ Детальная страница недоступна")
            continue
        
        print("     ✅ Детальная страница получена")
        
        # Ищем заголовок
        title_el = detail.select_one("h1")
        if title_el:
            title = title_el.get_text(strip=True)
            print(f"     📄 Заголовок: {title}")
        else:
            print("     ❌ Заголовок не найден")
        
        # Ищем даты
        time_el = detail.select_one("time[datetime]") or detail.find("time")
        if time_el:
            datetime_attr = time_el.get("datetime")
            time_text = time_el.get_text(strip=True)
            print(f"     📅 Time элемент: datetime='{datetime_attr}', text='{time_text}'")
        else:
            print("     ❌ Time элемент не найден")
            
            # Ищем даты в тексте
            date_texts = []
            for el in detail.find_all(string=True):
                text = str(el).strip()
                if any(year in text for year in ["2025", "2026", "2024"]):
                    date_texts.append(text)
            
            if date_texts:
                print(f"     📅 Найдены даты в тексте: {date_texts[:3]}")
            else:
                print("     ❌ Даты в тексте не найдены")

if __name__ == "__main__":
    test_bacc_detailed()
