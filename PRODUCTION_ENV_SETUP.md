# Production ENV Setup для WeekPlanner Wave-2

## Быстрая настройка

Создайте файл `.env` в корне проекта или экспортируйте переменные в shell:

```bash
# БД: локальный SQLite (MVP)
export DB_URL="sqlite:////$PWD/data/wp.db"

# Redis: managed инстанс (замени на свои данные)
export REDIS_URL="rediss://username:password@your-redis-host.com:6380/0"

# Город и кеш-политика
export CITY="bangkok"
export CACHE_TTL_S="1200"           # 20 минут
export CACHE_SWR_MARGIN_S="600"     # +10 минут stale-while-revalidate

# Снапшоты HTML (опционально, можно отключить)
export SNAPSHOT_ENABLE="true"
export SNAPSHOT_TOP_PERCENT="0.2"   # топ-20% карточек
export SNAPSHOT_DIR="$PWD/data/snapshots"

# (опционально) путь для QA JSON-отчёта
export QA_JSON_OUT="$PWD/qa_report.json"

# Дополнительные настройки ingestion
export FETCH_PAUSE_MS="1000"        # 1 секунда между источниками
export DAYS_AHEAD="7"               # Кэшировать на 7 дней вперед
```

## Где взять Redis

### Вариант 1: Upstash (бесплатно)
1. Зарегистрируйтесь на [upstash.com](https://upstash.com)
2. Создайте Redis базу данных
3. Скопируйте REDIS_URL из dashboard

### Вариант 2: Redis Cloud (бесплатно)
1. Зарегистрируйтесь на [redis.com](https://redis.com)
2. Создайте Cloud Database
3. Скопируйте connection string

### Вариант 3: Локальный Redis (для разработки)
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis-server

# Тогда REDIS_URL будет:
export REDIS_URL="redis://localhost:6379/0"
```

## Проверка настроек

```bash
# Загрузить ENV
source .env

# Проверить что переменные установлены
echo "DB_URL: $DB_URL"
echo "REDIS_URL: $REDIS_URL"
echo "CITY: $CITY"

# Тест подключения к Redis
python3 -c "
import redis
r = redis.Redis.from_url('$REDIS_URL', decode_responses=True)
print('Redis connection: OK')
"
```

## Структура директорий

```
week_planner/
├── data/
│   ├── wp.db              # SQLite база данных
│   ├── snapshots/         # HTML снапшоты
│   └── qa_report.json    # QA отчет (опционально)
├── .env                   # ENV переменные
└── ...
```

## Следующие шаги

После настройки ENV:
1. Запустить первичную загрузку данных
2. Проверить содержимое БД и Redis
3. Настроить расписание ingestion
