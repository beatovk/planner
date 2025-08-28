# Week Planner - CLI Diagnostic Tool

## Описание

`scripts/diag_verify.py` - это end-to-end диагностический инструмент для проверки всего пайплайна Week Planner.

## Что проверяет

1. **Fetchers Health**: Пробует подключиться к источникам данных
2. **Database**: Проверяет наличие событий в БД по датам/городу
3. **Category Mapping**: Анализирует покрытие флагами событий
4. **Redis Cache**: Инспектирует ключи кэша (основные + stale)
5. **Discrepancies**: Автоматически находит расхождения БД ↔ Redis

## Запуск

### Базовый запуск
```bash
export DB_URL="sqlite:///data/wp.db"
export REDIS_URL="redis://default:<PASS>@<HOST>:<PORT>"
python3 scripts/diag_verify.py --date 2025-08-31 --days 7
```

### С подсказкой по флагам
```bash
python3 scripts/diag_verify.py --date 2025-08-31 --days 7 --flags "art,culture,market"
```

### Параметры
- `--city`: город (по умолчанию "bangkok")
- `--date`: начальная дата в формате YYYY-MM-DD
- `--days`: количество дней для проверки
- `--flags`: подсказка по флагам (через запятую)

## Интерпретация отчёта

### 1. Scope
```json
"scope": {
  "city": "bangkok",
  "date_from": "2025-08-31",
  "days": 7,
  "date_to": "2025-09-06"
}
```
Показывает временной диапазон диагностики.

### 2. Fetchers Probe
```json
"fetchers_probe": [
  {
    "fetcher": "core.fetchers.bk_magazine",
    "health": "ok",
    "fetched_sample": 15
  }
]
```
- **Пустой массив**: фетчеры не найдены или не работают
- **Ошибки**: видны в поле `error`

### 3. Database
```json
"db": {
  "events_total": 2,
  "by_source": {"test": 2},
  "by_day": {"2025-01-28": 1, "2025-01-29": 1},
  "by_flag": {"art": 2},
  "unflagged_events": 0
}
```
- **events_total**: общее количество событий
- **by_source**: распределение по источникам
- **by_day**: распределение по дням
- **by_flag**: распределение по флагам
- **unflagged_events**: события без флагов (проблема маппера!)

### 4. Redis
```json
"redis": {
  "flags": {
    "art": {
      "2025-08-31": {
        "main": {"exists": false, "ttl": -1},
        "stale": {"exists": true, "ttl": 5176},
        "has_data": true
      }
    }
  }
}
```
- **main**: основной ключ (TTL 30 мин)
- **stale**: stale ключ (TTL 2+ часа)
- **has_data**: есть ли данные в любом ключе

### 5. Discrepancies
```json
"discrepancies": [
  {
    "day": "2025-01-28",
    "flag": "art",
    "problem": "DB has events for day/flag, Redis key empty or missing"
  }
]
```
Автоматически найденные проблемы:
- БД говорит "есть события", Redis говорит "пусто"
- Возможные причины: кэш не построен, ключи не те, TTL истёк

### 6. Likely Causes
```json
"likely_causes": [
  "Кэш не построен (или ключи не тем именем) для дней/флагов, хотя события в БД есть."
]
```
Автоматические гипотезы о проблемах на основе анализа.

## Типичные проблемы и решения

### 1. "Ingestion не записал события в БД"
- Проверьте логи ingestion
- Проверьте DB_URL и права доступа
- Проверьте фильтры по датам/городу

### 2. "Маппер категорий/флагов не помечает события"
- Все события имеют `unflagged_events > 0`
- Проверьте логику маппера
- Проверьте регулярные выражения

### 3. "Кэш не построен"
- Проверьте REDIS_URL
- Проверьте логи API
- Проверьте TTL настройки

### 4. "Redis ключи не те"
- Проверьте схему ключей в `core/cache.py`
- Проверьте `make_flag_key()` функцию

## Сохранение отчётов

Каждый запуск сохраняет отчёт в `diag/last_report.json` для дальнейшего анализа.

## Примеры использования

### Быстрая проверка текущего состояния
```bash
python3 scripts/diag_verify.py --date $(date +%Y-%m-%d) --days 1
```

### Диагностика проблем с кэшем
```bash
python3 scripts/diag_verify.py --date 2025-08-31 --days 7 --flags "art,culture,market"
```

### Проверка покрытия флагами
```bash
python3 scripts/diag_verify.py --date 2025-01-27 --days 30
```
