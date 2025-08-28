# Настройка ежедневного ingestion

## Вариант 1: Через переменные окружения

```bash
# Установить зависимости
pip install -r requirements.txt

# Настроить переменные окружения
export DB_URL="sqlite:///data/week_planner.db"
export REDIS_URL="redis://localhost:6379/0"
export CITY="bangkok"
export INTERVAL_MIN=1440  # 24 часа = раз в день
export CACHE_TTL_S=86400  # 24 часа
export CACHE_SWR_MARGIN_S=3600  # 1 час grace period

# Запустить планировщик
python scripts/run_ingest.py
```

## Вариант 2: Через cron (рекомендуется для production)

```bash
# Добавить в crontab (crontab -e)
# Запуск каждый день в 06:00 Asia/Bangkok time
0 6 * * * cd /path/to/week_planner && python scripts/run_ingest.py --once
```

## Вариант 3: Через systemd timer (Linux)

Создать файл `/etc/systemd/system/week-planner-ingest.service`:
```ini
[Unit]
Description=WeekPlanner Daily Ingestion
After=network.target

[Service]
Type=oneshot
User=weekplanner
WorkingDirectory=/path/to/week_planner
Environment=DB_URL=sqlite:///data/week_planner.db
Environment=REDIS_URL=redis://localhost:6379/0
Environment=CITY=bangkok
ExecStart=/usr/bin/python scripts/run_ingest.py --once
```

Создать файл `/etc/systemd/system/week-planner-ingest.timer`:
```ini
[Unit]
Description=Run WeekPlanner ingestion daily
Requires=week-planner-ingest.service

[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Затем:
```bash
sudo systemctl enable week-planner-ingest.timer
sudo systemctl start week-planner-ingest.timer
```

## Проверка работы

```bash
# Тест однократного запуска
python scripts/run_ingest.py --once

# Проверка тестов
pytest -q tests/test_ingest_scheduler.py

# Проверка статуса (если используете systemd)
sudo systemctl status week-planner-ingest.timer
```

## Логи

Ingestion логирует в stdout:
- `[ingest] upsert=N, cached_keys=M city=city`
- `[scheduler] started interval=Nmin`
- `[ingest] ERROR: ...` при ошибках

## HTML Снапшоты (опционально)

Для сохранения HTML снапшотов топ событий:

```bash
# Включить снапшоты
export SNAPSHOT_ENABLE=true

# Доля событий для снапшотов (по умолчанию 20%)
export SNAPSHOT_TOP_PERCENT=0.2

# Директория для снапшотов
export SNAPSHOT_DIR=/data/snapshots
```

**Важно:** Снапшоты не влияют на производительность API - они создаются только во время ingestion и сохраняются в `raw_html_ref` поле БД.
