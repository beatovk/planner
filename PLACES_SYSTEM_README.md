# Places System - "Вторая ножка" рекомендаций

## Обзор

Система Places предоставляет долговечные рекомендации мест без привязки к дате. Это дополняет существующую систему событий, создавая полноценную рекомендательную систему для планирования активностей.

## Архитектура

### 1. Модель данных

**Place** - основная сущность для мест:

```python
class Place(BaseModel):
    id: str                    # Уникальный идентификатор
    source: str                # Источник данных
    city: str                  # Город
    name: str                  # Название места
    description: str           # Описание
    url: str                   # URL места
    image_url: str             # URL изображения
    address: str               # Адрес
    lat/lon: float            # Координаты
    area: str                  # Район (Sukhumvit, Silom, etc.)
    price_level: int          # Уровень цен (0-4)
    tags: List[str]           # Теги
    flags: List[str]          # 11 флагов категорий
    popularity: float         # Популярность
    vec: List[float]          # Векторное представление (384D)
    created_at/updated_at     # Временные метки
```

### 2. Флаги категорий

Используются те же 11 флагов, что и для событий:

- `electronic_music` - электронная музыка, клубы
- `live_music` - живая музыка, концерты
- `jazz_blues` - джаз и блюз
- `rooftop` - крыши, бары с видом
- `food_dining` - рестораны, кафе, бары
- `art_exhibits` - галереи, музеи, выставки
- `workshops` - мастер-классы, обучение
- `cinema` - кинотеатры, фильмы
- `markets` - рынки, торговые центры
- `yoga_wellness` - йога, велнес, спа
- `parks` - парки, природа, прогулки

### 3. Источники данных

#### Timeout Bangkok
- **URL**: `https://www.timeout.com/bangkok/`
- **Категории**: рестораны, бары, достопримечательности, шоппинг, искусство, велнес
- **Селекторы**: адаптированы под структуру Timeout

#### BK Magazine
- **URL**: `https://bk.asia-city.com/bangkok/`
- **Категории**: рестораны, бары, искусство, шоппинг, велнес, достопримечательности
- **Селекторы**: адаптированы под структуру BK Magazine

#### Универсальный Fetcher
- Объединяет все источники
- Дедупликация по `identity_key`
- Параллельная обработка

### 4. Хранилище

#### База данных (SQLite/PostgreSQL)
```sql
CREATE TABLE places (
  id TEXT PRIMARY KEY,
  source TEXT,
  city TEXT,
  name TEXT,
  description TEXT,
  url TEXT,
  image_url TEXT,
  address TEXT,
  lat REAL, lon REAL,
  area TEXT,
  price_level INTEGER,
  tags TEXT,    -- JSON
  flags TEXT,   -- JSON
  popularity REAL,
  vec TEXT,     -- JSON
  identity_key TEXT UNIQUE,
  created_at TEXT, updated_at TEXT
);
```

**Индексы**:
- `idx_places_city` - по городу
- `idx_places_flags` - по флагам (JSON)
- `idx_places_area` - по району
- `idx_places_popularity` - по популярности

#### Redis кэш
- **Основной кэш**: `v1:places:<city>:flag:<flag>` (TTL: 1 час)
- **Stale кэш**: `v1:places:<city>:flag:<flag>:stale` (TTL: 24 часа)
- **Индекс**: `v1:places:<city>:index` - список закэшированных флагов

### 5. Сервисный слой

**PlacesService** объединяет:
- Fetcher'ы для получения данных
- База данных для хранения
- Redis для кэширования
- Логику дедупликации и фильтрации

## Использование

### 1. CLI инструменты

#### Инициализация БД
```bash
python scripts/places_cli.py init-db
```

#### Получение мест по флагам
```bash
python scripts/places_cli.py get-by-flags food_dining art_exhibits --limit 10
```

#### Получение мест по категории
```bash
python scripts/places_cli.py get-by-category food --limit 20
```

#### Прогрев кэша
```bash
python scripts/places_cli.py warm-cache --flags food_dining art_exhibits
```

#### Обновление данных
```bash
python scripts/places_cli.py refresh --flags food_dining
```

#### Статистика
```bash
python scripts/places_cli.py stats
```

### 2. Программное использование

```python
from core.places_service import PlacesService

service = PlacesService()

# Получить места по флагам
places = service.get_places_by_flags("bangkok", ["food_dining", "art_exhibits"])

# Получить места по категории
places = service.get_places_by_category("bangkok", "food")

# Прогреть кэш
results = service.warm_cache("bangkok", ["food_dining", "art_exhibits"])

# Получить статистику
stats = service.get_stats("bangkok")
```

### 3. API эндпоинты (планируется)

```python
# POST /api/places
{
  "city": "bangkok",
  "flags": ["food_dining", "art_exhibits"],
  "limit": 20
}

# POST /api/places/recommend
{
  "city": "bangkok",
  "user_preferences": ["food", "art"],
  "limit": 10
}
```

## Конфигурация

### Переменные окружения

```bash
# База данных мест
PLACES_DB_URL="sqlite:///./data/places.db"

# Redis
REDIS_URL="redis://localhost:6379/0"

# Настройки fetcher'ов
TO_CONCURRENCY=6
TO_TIMEOUT_S=8
BK_CONCURRENCY=4
BK_TIMEOUT_S=10
```

### Fallback значения

- **БД**: `./data/places.db` (SQLite)
- **Redis**: `redis://localhost:6379/0`

## Тестирование

### Запуск тестов
```bash
python test_places_system.py
```

### Тестируемые компоненты
- ✅ Модель Place
- ✅ Маппинг флагов
- ✅ Создание мест
- ✅ PlacesService (базовый функционал)

## Мониторинг и диагностика

### Метрики БД
- Общее количество мест
- Распределение по флагам
- Распределение по источникам

### Метрики кэша
- TTL для каждого флага
- Размер кэша в байтах
- Количество закэшированных флагов

### Логирование
- Уровень INFO для основных операций
- Уровень WARNING для проблем с источниками
- Уровень ERROR для критических ошибок

## Расширение системы

### 1. Новые источники
Создать класс, наследующий от `FetcherPlaceInterface`:

```python
class NewSourcePlacesFetcher(FetcherPlaceInterface):
    name = "new_source"
    
    def fetch(self, city: str, category: Optional[str] = None, limit: Optional[int] = None) -> List[Place]:
        # Реализация фетчинга
        pass
```

### 2. Новые категории
Добавить в `core/query/place_facets.py`:

```python
CATEGORY_RULES = {
    # ... существующие правила
    "new_category": ["keyword1", "keyword2"],
}
```

### 3. Новые города
Добавить поддержку в fetcher'ы и обновить селекторы.

## Производительность

### Оптимизации
- **Параллельный фетчинг** с ограничением concurrency
- **Кэширование** с fallback на stale данные
- **Индексы БД** для быстрого поиска
- **Дедупликация** по `identity_key`

### Ограничения
- **Fetcher'ы**: 4-6 параллельных запросов
- **Таймауты**: 8-10 секунд на запрос
- **Лимиты**: до 100 мест на флаг
- **TTL кэша**: 1 час (основной), 24 часа (stale)

## Безопасность

### Валидация данных
- Нормализация текста
- Валидация URL
- Проверка координат
- Санитизация тегов

### Ограничения доступа
- User-Agent заголовки для fetcher'ов
- Таймауты для предотвращения DoS
- Лимиты на количество запросов

## Заключение

Система Places успешно реализует "вторую ножку" рекомендаций:

✅ **Модель данных** - полноценная модель Place с валидацией  
✅ **Fetcher'ы** - Timeout Bangkok, BK Magazine, универсальный  
✅ **Хранилище** - SQLite/PostgreSQL + Redis кэш  
✅ **Сервисный слой** - PlacesService с полным функционалом  
✅ **CLI инструменты** - управление через командную строку  
✅ **Тестирование** - покрытие основных компонентов  
✅ **Документация** - полное описание системы  

**Система готова к использованию и расширению!** 🚀✨
