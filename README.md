# Week Planner - Places Discovery & Recommendation System

**Smart place discovery system for your daily plans**

The application analyzes your text request (e.g., "today I want to chill in a park, have ice cream and tom yum") and provides personalized place recommendations: parks for relaxation + cafes with ice cream + tom yum restaurants in the same area.

## 🎯 Core Functionality

### 🏞️ Smart Place Discovery by Context
- **Parks & Recreation**: green spaces, squares, waterfronts
- **Food & Beverages**: restaurants, cafes, street food
- **Entertainment**: museums, galleries, activities
- **Practical**: shops, services, transportation

### 🧠 AI-powered Recommendations
- Natural language query analysis
- Location, time, weather, mood consideration
- User preference personalization
- Area-based place grouping for convenience

### 🗺️ Real Data Integration
- Places API (Google, Foursquare, OpenStreetMap)
- Local place databases
- Up-to-date venue information
- User reviews and ratings

### 🌏 Multi-language Support
- **Primary**: English (default)
- **Secondary**: Thai (for Thailand operations)
- **Future**: Additional languages based on market expansion

## 🏗️ Architecture

### 📁 Project Structure
```
.
├─ apps/                    # Application entry points
│  ├─ api/                 # FastAPI web application
│  │   ├─ app_factory.py   # 🆕 App Factory (recommended)
│  │   ├─ main.py          # ⚠️ Old main.py (issues)
│  │   └─ static/          # Static files
│  ├─ cli/                 # CLI tools
│  └─ worker/              # Background processes
├─ packages/                # Business logic
│  ├─ wp_core/             # Shared utilities & configuration
│  │   └─ utils/           # Utilities (including feature flags)
│  ├─ wp_models/           # Pydantic models
│  ├─ wp_cache/            # Redis caching
│  ├─ wp_tags/             # Tag & category system
│  ├─ wp_places/           # 🏪 Places management (core functionality)
│  │   ├─ api.py           # 🆕 Places API routes
│  │   ├─ service.py       # Places business logic
│  │   └─ fetchers/        # Place data fetching
│  ├─ wp_events/           # ⏸️ Events management (temporarily disabled)
│  ├─ wp_services/         # High-level services
│  └─ wp_extract/          # Data extraction
├─ core/                    # Core logic
│   ├─ places_service.py   # Places service
│   └─ aggregator.py       # Data aggregation
├─ db/                      # Database schemas
├─ static/                  # Static resources
├─ tests/                   # Tests
└─ data/                    # Data storage
```

### 🔧 Key Components

#### **Places System (Core Functionality)**
- **PlacesService** - main service for places management
- **Tag Mapper** - category and tag system for place classification
- **Cache Layer** - Redis caching with circuit breaker
- **Fetchers** - data fetching from various sources

#### **App Factory Pattern**
- **Problem isolation** - syntax errors in main.py don't affect operation
- **Conditional route registration** - via feature flag `WP_DISABLE_EVENTS`
- **Flexibility** - easily enable/disable functionality

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Clone and setup
git clone <repo-url>
cd week_planner

# Setup environment variables
source setup_env.sh

# Install dependencies
make install-deps

# Install packages in development mode
make dev
```

### 2. Application Launch
```bash
# 🆕 Launch via App Factory (recommended)
make run-factory

# 🆕 Launch via new module system
make run
```

### 3. Port Management

#### Kill processes on port (Unix/macOS)
```bash
make kill-port
```

#### Kill processes on port (Windows)
```cmd
netstat -ano | findstr :8000
taskkill /PID <id> /F
```

# ⚠️ Old method (may contain errors)
make run

# Or directly
uvicorn apps.api.app_factory:create_app --factory --reload

## 🚨 Ситуации

### Порт занят
```bash
make kill-port  # Убивает процессы на порту
make run        # Запускает заново
```

**Что происходит**: Если порт 8000 уже занят, приложение покажет "красивую" ошибку вместо зависания.

**Решение**: `make kill-port` находит и убивает процессы на порту, затем `make run` запускает заново.

**Проверка**: После `make kill-port` порт должен освободиться (`lsof -i :8000` возвращает пустой результат).

### Старый код
**Проблема**: Запускаешь через `python main.py` или `python apps/api/main.py`  
**Решение**: Используй `python -m apps.api` или `make run`

**Проверка**: В терминале должно быть `python -m apps.api`, а не старые пути.

### Кэш холодный
```bash
make warm-cache  # Разогревает кэш sample-запросами
```

### Быстрая проверка
```bash
make check       # Проверяет health endpoint
make dev-test    # Быстрый прогон основных тестов
```

## 🔄 Частые сценарии

### 🚀 Запуск без внешних зависимостей
```bash
# Приложение использует простой in-memory кэш
# Никаких внешних сервисов не требуется

# Запуск в фоновом режиме (рекомендуется)
make start-server    # Запускаем сервер в фоне
make stop-server     # Останавливаем сервер

# Обычный запуск
make run             # Запускаем с простым кэшем
make dev-run         # Запускаем с auto-reload
```

### 🔥 Прогрев кэша
```bash
make warm-cache      # Разогревает кэш популярными запросами
# Или вручную:
curl "http://localhost:8000/api/places/recommend?mood=lazy_outdoor"
curl "http://localhost:8000/api/places/recommend?mood=relaxed"
```

### 🧪 Запуск тестов
```bash
make test            # Все unit тесты
make lint            # Проверка кода (ruff)
make guard           # Блокировка deprecated кода
make dev-test        # Быстрые dev тесты
```

### 🚨 Защита от регрессий
```bash
make guard           # Проверяет, что deprecated код не вернулся
# Блокирует:
# - DEPRECATED_*.py файлы
# - core/ и src/ директории
# - Старые импорты
```

### 3. API Testing
```bash
# 🏪 Places API (working)
curl "http://localhost:8000/api/places?city=bangkok&flags=parks&limit=6"
curl "http://localhost:8000/api/places/categories"
curl "http://localhost:8000/api/places/stats"

# ⏸️ Events API (temporarily disabled)
curl "http://localhost:8000/api/events"  # → 503 Service Unavailable
curl "http://localhost:8000/api/plan"    # → 503 Service Unavailable
```

### 4. Health Check
```bash
# Places system smoke test
make smoke-places

# Places tests
make test-places

# CI tests
make ci-places
```

## 🔧 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_URL` | SQLite database path | `sqlite:///data/wp.db` |
| `REDIS_URL` | ~~Redis connection string~~ **REMOVED** | ~~`redis://localhost:6379/0`~~ |
| `CITY` | Default city | `bangkok` |
| `CACHE_TTL_S` | Cache TTL in seconds | `1200` |
| `WP_ENABLE_ADMIN` | Enable admin endpoints | `false` |
| `WP_TIMEZONE` | Application timezone | `Asia/Bangkok` |
| **`WP_DISABLE_EVENTS`** | **Disable events functionality** | **`0`** |

### 🚨 Important Variable: `WP_DISABLE_EVENTS`

```bash
# Disable events (Places API only)
export WP_DISABLE_EVENTS=1

# Enable events (Places + Events API)
export WP_DISABLE_EVENTS=0
```

**When `WP_DISABLE_EVENTS=1`:**
- ✅ Places API works fully
- ❌ Events API returns 503 Service Unavailable
- 🔒 Event ingestion disabled
- 🚫 Event schedulers don't start

## 📊 Caching Policy

### 🏪 Places Cache (active)
- **Hot Cache**: `v1:places:<city>:flag:<flag>` (TTL: 20min)
- **Stale Cache**: `v1:places:<city>:flag:<flag>:stale` (TTL: 10min)
- **Index**: `v1:places:<city>:index` (TTL: 30min)

### ⏸️ Events Cache (temporarily disabled)
- **Hot Cache**: `v2:<city>:<YYYY-MM-DD>:flag:<flag>` (TTL: 20min)
- **Stale Cache**: `v2:<city>:<YYYY-MM-DD>:flag:<flag>:stale` (TTL: 10min)
- **Index**: `v2:<city>:<YYYY-MM-DD>:index` (TTL: 30min)

### 🔄 Circuit Breaker
- **Redis bypass** on failures
- **Database fallback** when cache is unavailable
- **Automatic recovery** after Redis restoration

## 🛠️ Development

### 📋 Available Commands
```bash
make help          # Show all commands
make dev           # Install packages in development mode
make run-factory   # 🆕 Launch server via App Factory (recommended)
make run           # ⚠️ Launch server via old main.py
make test          # Run all tests
make test-places   # 🏪 Test Places functionality
make test-redis    # 🔴 Test Redis functionality
make ci-places     # 🚀 CI tests for Places
make smoke-places  # 🔍 Quick Places system check
make ingest        # ⏸️ Run event ingestion (disabled when WP_DISABLE_EVENTS=1)
make prewarm       # Warm up cache
make diag          # Run diagnostics
make clean         # Clean temporary files
```

### 🧪 Testing

#### **Places System (recommended)**
```bash
# Main Places tests
make test-places

# Redis functionality
make test-redis

# CI tests
make ci-places

# Quick check
make smoke-places
```

#### **Full Test Suite**
```bash
# ⚠️ May contain errors due to problematic main.py
make test
```

## 🎯 Core Functionality - Places Discovery

### 🏞️ What the System Does

Week Planner is a **smart place discovery system** for your daily plans. Instead of event planning, the application focuses on **personalized place recommendations** based on your requests.

### 💡 Usage Examples

#### **Scenario 1: Park Relaxation + Food**
```
Request: "today I want to chill in a park, have ice cream and tom yum"

Result:
🏞️ Parks for relaxation:
  - Lumpini Park (green space, benches, shady alleys)
  - Benjakitti Park (lake, bicycle paths)

🍦 Ice cream nearby:
  - Swensen's (5 min from Lumpini)
  - Baskin-Robbins (3 min from Benjakitti)

🍜 Tom yum in the area:
  - Tom Yum Kung (authentic tom yum, 7 min from park)
  - Siam Tom Yum (modern presentation, 4 min from park)
```

#### **Scenario 2: Cultural Day**
```
Request: "I want to visit a museum, then sit in a cozy cafe"

Result:
🏛️ Museums:
  - Bangkok National Museum (Thai history)
  - Jim Thompson House (Thai silk)

☕ Cafes nearby:
  - Blue Whale Cafe (cozy atmosphere, 3 min from museum)
  - Gallery Drip Coffee (coffee + art, 5 min from museum)
```

### 🧠 How It Works

1. **Query Analysis** - system understands your intentions in natural language
2. **Place Search** - finds relevant places by categories and tags
3. **Area Grouping** - combines places into logical routes
4. **Personalization** - considers your preferences and history
5. **Recommendations** - suggests optimal place combinations

### 🏷️ Category System

- **🏞️ Parks & Recreation**: `parks`, `recreation`, `nature`
- **🍽️ Food & Beverages**: `food_dining`, `cafes`, `restaurants`
- **🎭 Culture**: `museums`, `galleries`, `theaters`
- **🛍️ Shopping**: `shopping`, `markets`, `malls`
- **🚇 Transport**: `transport`, `parking`, `stations`
- **🏥 Services**: `services`, `healthcare`, `education`

## 🚀 API Endpoints

### 🏪 Places API (working)

```bash
# Get places by categories
GET /api/places?city=bangkok&flags=parks,food_dining&limit=10

# Get available categories
GET /api/places/categories

# Places statistics
GET /api/places/stats?city=bangkok

# Warm up cache for category
POST /api/places/warm-cache?city=bangkok&flags=parks
```

### ⏸️ Events API (temporarily disabled)

```bash
# All event endpoints return 503 Service Unavailable
GET /api/events          # → 503 "Events temporarily disabled"
POST /api/plan           # → 503 "Planner (events) disabled"
GET /api/live-events     # → 503 "Live events temporarily disabled"
```

## 📊 Current Project Status

### ✅ What Works

- **🏪 Places System** - fully functional
  - Places API with 4 endpoints
  - Category and tag system
  - Redis caching with circuit breaker
  - Places database
  - Tests and CI

- **🔧 App Factory Pattern** - solves import issues
  - Isolation from problematic main.py
  - Conditional route registration
  - Flexible configuration

- **🚀 Feature Flags** - functionality management
  - `WP_DISABLE_EVENTS` for disabling events
  - Safe testing
  - CI/CD readiness

### ⏸️ What's Temporarily Disabled

- **Events System** - disabled via feature flag
  - Event ingestion
  - Event schedulers
  - Event API endpoints
  - Event caching

### 🚧 What's in Development

- **AI-powered query analysis** - natural language understanding
- **Personalization** - user preference consideration
- **Area-based grouping** - logical routes
- **External API integration** - Google Places, Foursquare

### 🎯 Development Plans

#### **Short-term (1-2 months)**
1. **Places API improvements** - more filters and sorting
2. **Places database expansion** - more cities and categories
3. **Caching optimization** - performance improvements

#### **Medium-term (3-6 months)**
1. **AI query analysis** - understanding user intentions
2. **Personalization** - recommendations based on history
3. **Mobile application** - convenient interface

#### **Long-term (6+ months)**
1. **Calendar integration** - day planning
2. **Social features** - sharing plans with friends
3. **Multi-language support** - additional language support

## 🔗 Useful Links

- **📚 App Factory README** - `APPS_FACTORY_README.md`
- **🏪 Places System README** - `PLACES_SYSTEM_README.md`
- **🔧 Makefile** - all available commands
- **🧪 Tests** - `tests/` directory

## 🤝 Contributing

### 🐛 Report an Issue
1. Check that the issue is not related to disabled events
2. Make sure you're using `make run-factory`
3. Check the `WP_DISABLE_EVENTS` variable

### 💡 Suggest Improvements
1. Describe the desired functionality
2. Provide usage examples
3. Indicate priority

---

**Status**: 🚀 Places System ready for use  
**Recommendation**: Use `make run-factory` to launch  
**Feature Flag**: `WP_DISABLE_EVENTS=1` to disable events

### 📦 Package Development

The project uses a modular package structure for better organization and maintainability. Each package can be developed and tested independently.

#### Development Mode Installation
```bash
# Install all packages in development mode
make dev

# Or install individual packages
pip install -e packages/wp_core
pip install -e packages/wp_places
pip install -e packages/wp_events
```

#### Package Structure
Each package follows a standard structure:
- `__init__.py` - Package initialization and exports
- `setup.py` - Package configuration and dependencies
- `README.md` - Package documentation
- `tests/` - Package tests

#### Testing Individual Packages
```bash
# Test specific package
pytest packages/wp_places/tests/
pytest packages/wp_core/tests/

# Test with coverage
pytest --cov=packages/wp_places
```

## 🔄 Migration from Old Structure

Old modules `core/*` and `src/*` are available as compatibility shims:

```python
# Old way (deprecated)
from core.places_service import PlacesService

# New way
from packages.wp_places.service import PlacesService
```

Shims emit `DeprecationWarning` but maintain full compatibility.

## 📈 Performance

- **Cache Hit Rate**: >90% for repeated requests
- **Response Time**: <100ms for cached data
- **Database Queries**: Optimized with FTS5 indexing
- **Redis Operations**: Circuit breaker protection

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes following package structure
4. Add tests
5. Submit pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🆘 Support

If you have questions or issues:

1. **Check documentation** - this README and related files
2. **Use correct commands** - `make run-factory` instead of `make run`
3. **Check feature flags** - `WP_DISABLE_EVENTS` for functionality management
4. **Run tests** - `make ci-places` for health check

---

**Week Planner** - Smart place discovery system for your daily plans 🚀
