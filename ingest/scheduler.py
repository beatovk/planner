from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from apscheduler.schedulers.background import BackgroundScheduler
from packages.wp_core.utils.flags import events_disabled

from collections import Counter
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger("ingest")

# Event-related imports protected by feature flag
if not events_disabled():
    from packages.wp_events.aggregator import collect_events
    from packages.wp_models.event import Event
from storage.db import Database
from storage.cache import (
    get_redis,
    key_for_category,
    key_for_flag,
    cache_set_candidates,
)
from storage.snapshots import should_snapshot, build_snapshot_path, save_snapshot

# ---- Config helpers ---------------------------------------------------------

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except Exception:
        return default

def _env_str(name: str, default: str) -> str:
    return os.environ.get(name, default)

# ---- Retry/Rate-limit -------------------------------------------------------

def _sleep_ms(ms: int) -> None:
    if ms > 0:
        time.sleep(ms / 1000.0)

def _with_retry(fn, *, retries: int = 3, backoff_ms: int = 300) -> None:
    delay = 0
    for attempt in range(1, retries + 1):
        try:
            if delay:
                _sleep_ms(delay)
            return fn()
        except Exception as exc:
            if attempt == retries:
                raise
            delay = backoff_ms * attempt

# ---- Cache building ---------------------------------------------------------

def _group_ids_by_category_and_flags(
    events: List[Event],
    *,
    city: str,
    days: Iterable[datetime],
) -> Dict[str, List[str]]:
    """
    Собирает ключи вида:
      - city:YYYY-MM-DD:category -> [event_ids]
      - city:YYYY-MM-DD:flag:<flag> -> [event_ids]
    """
    keys: Dict[str, List[str]] = {}
    day_set = {d.date().isoformat() for d in days}
    for ev in events:
        if not ev.start:
            continue
        d = ev.start.date().isoformat()
        if d not in day_set:
            continue
        # categories
        for c in (ev.categories or []):
            k = key_for_category(city, d, c)
            keys.setdefault(k, []).append(ev.id)
        # boolean flags from attrs
        for flag, val in (ev.attrs or {}).items():
            if isinstance(val, bool) and val:
                k = key_for_flag(city, d, flag)
                keys.setdefault(k, []).append(ev.id)
    # сохраняем порядок id (как пришли), без дедупа — ingestion уже дедупит по identity
    
    # Добавляем пустые кэши для всех дат в диапазоне (даже без событий)
    for day in day_set:
        # Создаем базовый ключ для даты
        base_key = f"{city}:{day}"
        if base_key not in keys:
            keys[base_key] = []
    
    return keys

# ---- Main ingestion pass ----------------------------------------------------

def run_ingest_once(
    *,
    db_url: str | None = None,
    redis_url: str | None = None,
    city: str | None = None,
    days_ahead: int = 2,
) -> None:
    """
    Один прогон: собрать → дедуп в aggregator → upsert в БД → построить кэши в Redis.
    """
    db_url = db_url or _env_str("DB_URL", "")
    if not db_url:
        raise RuntimeError("DB_URL is required")
    redis_url = redis_url or _env_str("REDIS_URL", "")
    if not redis_url:
        raise RuntimeError("REDIS_URL is required")
    city = (city or _env_str("CITY", "bangkok")).lower()

    # Пауза между источниками (если fetchers её уважают)
    pause_ms = _env_int("FETCH_PAUSE_MS", 400)
    ttl_s = _env_int("CACHE_TTL_S", 1200)          # ~20 мин
    swr_s = _env_int("CACHE_SWR_MARGIN_S", 300)    # ~5 мин

    # Собрать события (включая дедуп/merge и QA внутри collect_events)
    def _collect():
        return collect_events()
    events: List[Event] = []
    _with_retry(lambda: events.extend(_collect()), retries=3, backoff_ms=400)
    _sleep_ms(pause_ms)
    
    # Диагностика: подсчёты до фильтрации по датам/городу
    by_source = Counter(e.source for e in events)
    log.info("[ingest] fetched raw events per source: %s", dict(by_source))
    
    # фильтрация по дате (сегодня..+days_ahead) + диагностика пропусков
    from datetime import datetime, timedelta, timezone
    tz = timezone.utc
    today = datetime.now(tz).date()
    last = today + timedelta(days=days_ahead)
    in_range = []
    drop_reasons = Counter()
    for ev in events:
        if not ev.start:
            drop_reasons["no_start"] += 1
            continue
        d = ev.start.date()
        if not (today <= d <= last):
            drop_reasons["out_of_range"] += 1
            continue
        if not ev.url:
            drop_reasons["no_url"] += 1
            continue
        in_range.append(ev)
    events = in_range
    log.info("[ingest] kept %d events; dropped=%s", len(events), dict(drop_reasons))

    # Опциональные HTML-снапшоты (top-N по проценту)
    snap_enable = _env_str("SNAPSHOT_ENABLE", "false").lower() == "true"
    snap_percent = float(_env_str("SNAPSHOT_TOP_PERCENT", "0.2"))
    snap_dir = _env_str("SNAPSHOT_DIR", "/data/snapshots")
    if snap_enable and events:
        now = datetime.now(timezone.utc)
        total = len(events)
        for i, ev in enumerate(events):
            if not getattr(ev, "url", None):
                continue
            if not should_snapshot(total, i, top_percent=snap_percent):
                continue
            rel = build_snapshot_path(ev.id, now, snap_dir)
            abs_path = str(Path(snap_dir) / rel)
            try:
                save_snapshot(str(ev.url), abs_path)
                # сохраняем относительный путь (от base_dir), чтобы переносить каталог проще
                ev.raw_html_ref = rel
            except Exception as exc:
                # не критично для ingestion; просто пропускаем
                print(f"[snapshot] WARN cannot save for {ev.id}: {exc}")

    # Запись в БД
    db = Database(db_url)
    db.create_tables()
    count = db.upsert_events(events, city=city)
    db.record_ingest(source="all", count=count, ok=True, note="ingest_once")

    # Построить ключи для сегодня..N дней вперёд
    now = datetime.now(timezone.utc)
    days = [now + timedelta(days=delta) for delta in range(0, max(0, days_ahead) + 1)]
    mapping = _group_ids_by_category_and_flags(events, city=city, days=days)

    # Запись в Redis
    r = get_redis(redis_url)
    for key, ids in mapping.items():
        cache_set_candidates(r, key, ids, ttl_s=ttl_s, swr_margin_s=swr_s)

    print(f"[ingest] upsert={count}, cached_keys={len(mapping)} city={city}")

# ---- Scheduler bootstrap ----------------------------------------------------

def start_scheduler() -> None:
    """
    Запускает планировщик по интервалу INTERVAL_MIN (по умолчанию 30).
    Для режима «раз в день» поставь INTERVAL_MIN=1440.
    """
    # Don't start event ingestion if events are disabled
    if events_disabled():
        print("[scheduler] Events disabled, skipping event ingestion scheduler")
        return
        
    db_url = _env_str("DB_URL", "")
    redis_url = _env_str("REDIS_URL", "")
    if not db_url or not redis_url:
        raise RuntimeError("DB_URL and REDIS_URL are required")
    interval_min = _env_int("INTERVAL_MIN", 30)

    sched = BackgroundScheduler(timezone="UTC")
    def job():
        try:
            if not events_disabled():
                run_ingest_once(db_url=db_url, redis_url=redis_url, city=_env_str("CITY", "bangkok"))
            else:
                print("[ingest] Events disabled, skipping ingestion")
        except Exception as exc:
            # «мягкая» обработка — логируем и продолжаем
            print(f"[ingest] ERROR: {exc}")
    sched.add_job(job, "interval", minutes=interval_min, id="ingest_all", max_instances=1, coalesce=True)
    sched.start()
    print(f"[scheduler] started interval={interval_min}min")
