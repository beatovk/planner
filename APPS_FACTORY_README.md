# App Factory Pattern для Week Planner API

## 🎯 Зачем нужен App Factory

App Factory паттерн решает несколько критических проблем:

1. **Циклические импорты** - избегаем проблем с `main.py` импортирующим модули, которые импортируют его
2. **Синтаксические ошибки** - изолируем проблемные модули от основного приложения
3. **Условная регистрация роутов** - легко включаем/выключаем функциональность через фичефлаги
4. **Тестируемость** - можно создавать разные конфигурации приложения для тестов

## 🏗️ Архитектура

### Структура файлов

```
apps/api/
├── app_factory.py      # 🆕 Основная фабрика приложений
├── main.py            # ⚠️ Проблемный файл (синтаксические ошибки)
└── routes/            # 📁 Роуты (будущее)
    └── places.py      # 🏪 Places API роуты

packages/wp_places/
├── api.py             # 🆕 Регистрация places роутов
├── service.py         # 🔧 Бизнес-логика
└── ...
```

### App Factory (`apps/api/app_factory.py`)

```python
def create_app() -> FastAPI:
    app = FastAPI()
    
    # Всегда регистрируем places роуты
    register_places_routes(app)
    
    # Условно регистрируем event роуты
    if not events_disabled():
        # register_event_routes(app)  # TODO: когда будет готово
        pass
    else:
        # Добавляем stub эндпоинты
        add_event_stub_endpoints(app)
    
    return app
```

### Places API (`packages/wp_places/api.py`)

```python
def register_places_routes(app: FastAPI) -> None:
    """Регистрирует все places роуты"""
    
    @app.get("/api/places")
    def api_places(city: str = "bangkok", flags: str = "", limit: int = 50):
        # Реализация получения мест
        
    @app.get("/api/places/categories")
    def api_places_categories():
        # Реализация получения категорий
        
    # ... другие роуты
```

## 🚀 Использование

### Запуск через App Factory (рекомендуется)

```bash
# Используя Makefile
make run-factory

# Или напрямую
uvicorn apps.api.app_factory:create_app --factory --reload
```

### Запуск через старый main.py (не рекомендуется)

```bash
# Может содержать синтаксические ошибки
make run

# Или напрямую
uvicorn apps.api.main:app --reload
```

## 🔧 Конфигурация

### Фичефлаг `WP_DISABLE_EVENTS`

```bash
# Отключить события (только places)
export WP_DISABLE_EVENTS=1
make run-factory

# Включить события (places + events)
export WP_DISABLE_EVENTS=0
make run-factory
```

### Роуты в зависимости от фичефлага

#### При `WP_DISABLE_EVENTS=1` (только places):
- ✅ `/api/places` - получение мест
- ✅ `/api/places/categories` - категории
- ✅ `/api/places/stats` - статистика
- ✅ `/api/places/warm-cache` - прогрев кеша
- ❌ `/api/events` → 503 "Events temporarily disabled"
- ❌ `/api/plan` → 503 "Planner (events) disabled"
- ❌ `/api/live-events` → 503 "Live events temporarily disabled"
- ❌ `/api/plan-cards` → 503 "Plan cards (events) disabled"
- ❌ `/api/day-cards` → 503 "Day cards (events) disabled"
- ❌ `/api/categories` → 503 "Event categories temporarily disabled"
- ❌ `/api/sources` → 503 "Event sources temporarily disabled"
- ❌ `/api/debug/source-ping` → 503 "Source ping (events) disabled"

#### При `WP_DISABLE_EVENTS=0` (places + events):
- ✅ `/api/places` - все places роуты
- ✅ `/api/events` - события (когда будет готово)
- ✅ `/api/plan` - планировщик (когда будет готово)
- ✅ Все остальные event роуты

## 🧪 Тестирование

### Тестирование App Factory

```bash
# Тест импорта
python3 -c "from apps.api.app_factory import create_app; print('✅ Import OK')"

# Тест создания приложения
python3 -c "from apps.api.app_factory import create_app; app = create_app(); print(f'Routes: {len(app.routes)}')"

# Тест с отключенными событиями
WP_DISABLE_EVENTS=1 python3 -c "from apps.api.app_factory import create_app; app = create_app(); print('✅ Events disabled OK')"

# Тест с включенными событиями
WP_DISABLE_EVENTS=0 python3 -c "from apps.api.app_factory import create_app; app = create_app(); print('✅ Events enabled OK')"
```

### Запуск тестов Places

```bash
# Основной таргет для CI
make ci-places

# Отдельные тесты
make test-places
make test-redis
make smoke-places
```

## 🔄 Миграция

### Пошаговый план

1. ✅ **Создан App Factory** - `apps/api/app_factory.py`
2. ✅ **Создан Places API** - `packages/wp_places/api.py`
3. ✅ **Добавлен Makefile таргет** - `make run-factory`
4. 🔄 **Тестирование** - проверка работоспособности
5. 📝 **Документация** - этот README
6. 🚀 **Продакшн** - переход на app factory
7. 🧹 **Очистка** - удаление проблемного main.py

### Текущий статус

- ✅ App Factory работает корректно
- ✅ Places роуты регистрируются
- ✅ Фичефлаг работает
- ✅ Stub эндпоинты для событий
- ⚠️ Старый main.py содержит синтаксические ошибки

## 🎯 Преимущества App Factory

1. **Изоляция проблем** - синтаксические ошибки в main.py не влияют на app factory
2. **Гибкость** - легко включать/выключать функциональность
3. **Тестируемость** - можно создавать разные конфигурации для тестов
4. **Масштабируемость** - легко добавлять новые модули
5. **Чистая архитектура** - разделение ответственности

## 🚨 Важные замечания

1. **Не используйте `make run`** - может содержать синтаксические ошибки
2. **Используйте `make run-factory`** - безопасный способ запуска
3. **Проверяйте фичефлаг** - `WP_DISABLE_EVENTS` контролирует функциональность
4. **Тестируйте перед деплоем** - используйте `make ci-places`

## 🔮 Будущее

1. **Event API модуль** - создание `packages/wp_events/api.py`
2. **Роуты в отдельных файлах** - `apps/api/routes/places.py`, `apps/api/routes/events.py`
3. **Конфигурация через переменные окружения** - более гибкая настройка
4. **Middleware и плагины** - расширение функциональности
5. **Мониторинг и метрики** - добавление observability

---

**Статус**: ✅ Готово к использованию  
**Рекомендация**: Используйте `make run-factory` вместо `make run`
