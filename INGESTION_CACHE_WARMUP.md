# Week Planner - Ingestion с прогревом кэша

## Обзор

Новый скрипт `scripts/ingest.py` интегрирует ingestion данных с автоматическим прогревом кэша по новым флагам. Использует универсальный facets mapper для автоматического определения категорий событий.

## Возможности

### 1. **Автоматический маппинг событий**
- Анализ title, description, tags
- 11 новых категорий с ключевыми словами
- Поддержка множественных флагов для одного события

### 2. **Прогрев кэша**
- Основные ключи: `v2:<city>:<date>:flag:<flag>`
- Stale ключи: `v2:<city>:<date>:flag:<flag>:stale`
- Индексы дней: `v2:<city>:<date>:index`

### 3. **Гибкая настройка**
- Диапазон дат (вперёд/назад)
- Выборочные флаги или все по умолчанию
- Dry-run режим для планирования

## Новые флаги

```python
DEFAULT_FLAGS = [
    "electronic_music",    # electronic, dj, club
    "live_music",         # live music, gig, band
    "jazz_blues",         # jazz, blues
    "rooftop",            # rooftop, view, skybar, bar
    "food_dining",        # food, thai food, street food, dining, restaurant
    "art_exhibits",       # art, exhibition, gallery, museum
    "workshops",          # workshop, learning, craft, class, course
    "cinema",             # cinema, movie, film, screening
    "markets",            # market, mall, shopping, bazaar, fair
    "yoga_wellness",      # yoga, meditation, wellness, retreat
    "parks",              # park, walk, nature, outdoor, garden
]
```

## Использование

### Базовый запуск

```bash
export DB_URL="sqlite:///data/wp.db"
export REDIS_URL="redis://default:<PASS>@<HOST>:<PORT>"

# Прогрев на 14 дней вперёд + 7 дней назад
python3 scripts/ingest.py --days-ahead 14 --days-back 7 --city bangkok
```

### С выборочными флагами

```bash
# Только арт и фуд события
python3 scripts/ingest.py --days-ahead 7 --flags "art_exhibits,food_dining"
```

### Dry-run режим

```bash
# Показать план без выполнения
python3 scripts/ingest.py --days-ahead 7 --days-back 3 --dry-run
```

### Параметры

- `--start-date`: начальная дата (YYYY-MM-DD), по умолчанию сегодня
- `--days-ahead`: количество дней вперёд (по умолчанию 14)
- `--days-back`: количество дней назад (по умолчанию 0)
- `--city`: город для обработки (по умолчанию "bangkok")
- `--flags`: флаги для прогрева через запятую (по умолчанию все)
- `--dry-run`: показать план без выполнения

## Примеры использования

### 1. **Еженедельный прогрев**

```bash
# Каждое воскресенье прогреваем на неделю вперёд
python3 scripts/ingest.py --days-ahead 7 --city bangkok
```

### 2. **Захват прошлых событий**

```bash
# Прогреваем на неделю назад + 2 недели вперёд
python3 scripts/ingest.py --days-ahead 14 --days-back 7 --city bangkok
```

### 3. **Топ-категории**

```bash
# Прогреваем только популярные категории
python3 scripts/ingest.py --days-ahead 7 --flags "art_exhibits,food_dining,markets,rooftop"
```

### 4. **Конкретная дата**

```bash
# Прогрев для конкретного события
python3 scripts/ingest.py --start-date 2025-01-27 --days-ahead 3 --days-back 1
```

## Архитектура

### Слои системы

1. **Data Layer**
   - SQLite/PostgreSQL через DatabaseFetcher
   - Fallback на прямой SQLite
   - Фильтрация по датам и городу

2. **Mapping Layer**
   - `map_event_to_flags()` из `core/query/facets.py`
   - Автоматическое определение категорий
   - Fallback на упрощённые правила

3. **Cache Layer**
   - `ensure_client()` из `core/cache.py`
   - `write_flag_ids()` для флагов
   - `update_index()` для индексов дней

### Поток данных

```
БД → События → Маппинг → Флаги → Кэш (Redis)
  ↓
Индексы дней с подсчётами
```

## Мониторинг

### Логи

```bash
# Подробные логи прогрева
python3 scripts/ingest.py --days-ahead 7 2>&1 | grep "ingest"

# Логи кэша
python3 scripts/ingest.py --days-ahead 7 2>&1 | grep "cache"
```

### Диагностика

```bash
# Проверка покрытия кэша
python3 scripts/diag_verify.py --date $(date +%F) --days 7 \
  --flags "electronic_music,live_music,jazz_blues,rooftop,food_dining,art_exhibits,workshops,cinema,markets,yoga_wellness,parks"
```

### Метрики

- **События по дням**: количество обработанных событий
- **Покрытие флагами**: распределение по категориям
- **Время выполнения**: общая производительность
- **Ошибки**: проблемы с БД/Redis

## Интеграция

### 1. **С существующим ingestion**

```python
# В ingest/scheduler.py можно добавить вызов
from scripts.ingest import warmup_cache

def run_ingest_once():
    # ... существующий код ...
    
    # Дополнительный прогрев кэша
    warmup_cache(city, dates, DEFAULT_FLAGS)
```

### 2. **С планировщиком**

```bash
# Cron job для автоматического прогрева
0 2 * * 0 cd /path/to/week_planner && \
  python3 scripts/ingest.py --days-ahead 14 --days-back 7
```

### 3. **С API**

```python
# В main.py уже есть endpoint для prewarm
@app.post("/api/prewarm")
async def api_prewarm():
    from scripts.ingest import warmup_cache
    # ... вызов warmup_cache
```

## Troubleshooting

### Частые проблемы

1. **"DatabaseFetcher failed"**
   - Нормально, используется fallback на SQLite
   - Проверьте что `data/wp.db` существует

2. **"Redis connection failed"**
   - Проверьте `REDIS_URL`
   - Убедитесь что Redis доступен

3. **"No events found"**
   - Проверьте диапазон дат
   - Убедитесь что в БД есть события

4. **"Import errors"**
   - Запускайте из корня проекта
   - Проверьте зависимости

### Отладка

```bash
# Подробные логи
export PYTHONPATH=.
python3 -u scripts/ingest.py --days-ahead 1 --days-back 1 2>&1 | tee ingest.log

# Проверка кэша
redis-cli -u $REDIS_URL KEYS "v2:bangkok:*"
```

## Производительность

### Оптимизации

1. **Batch операции**: все флаги для дня обрабатываются за раз
2. **TTL настройки**: 30 мин для основных, 2 часа для stale
3. **Fallback механизмы**: graceful degradation при ошибках

### Мониторинг

- **Время выполнения**: обычно 1-5 секунд на день
- **Память**: минимальное использование
- **Сеть**: только Redis операции

## Следующие шаги

### 1. **Расширение категорий**
- Добавить тайские ключевые слова
- Новые категории по мере необходимости
- ML-маппинг для сложных случаев

### 2. **Оптимизация**
- Параллельная обработка дней
- Кэширование результатов маппинга
- Batch Redis операции

### 3. **Мониторинг**
- Метрики качества маппинга
- Алерты на пустые флаги
- Dashboard для отслеживания

## Заключение

✅ **Ingestion с прогревом кэша полностью готов**

- **Функциональность**: автоматический маппинг + прогрев кэша
- **Интеграция**: использует существующую систему кэширования
- **Гибкость**: настраиваемые диапазоны и флаги
- **Надёжность**: fallback механизмы и обработка ошибок

**Система готова к автоматическому построению кэша для всех новых категорий!** 🚀✨
