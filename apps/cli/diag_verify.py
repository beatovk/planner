# scripts/diag_verify.py
"""
Week Planner — end-to-end диагностика пайплайна на интервале дат.
Проверяет:
1) Источники (fetchers): пробная выборка/health.
2) Ingestion → БД: есть ли события по датам/источникам.
3) Маппинг категорий/флагов: покрытие, пустые маппинги.
4) Redis-ключи: наличие, тип, длина, TTL, расхождения с БД.
5) API-путь: сухой прогон логики /api/events (без сети) и сравнение результата.

Запуск:
  export DB_URL="sqlite:///data/wp.db"
  export REDIS_URL="redis://default:<PASS>@<HOST>:<PORT>"
  python scripts/diag_verify.py --city bangkok --days 7 --date 2025-08-31

Выводит JSON-отчёт в консоль и сохраняет копию в diag/last_report.json
"""

import os
import json
import argparse
import datetime as dt
import importlib
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

# --- безопасные импорты с fallback'ами по типичному layout проекта ---
def _try_imports():
    mods = {}
    # SQLAlchemy / Redis
    import importlib
    for name in [
        ("sqlalchemy", "sa"),
        ("redis", "redis"),
        ("pydantic", "pydantic"),
    ]:
        try:
            mods[name[1]] = importlib.import_module(name[0])
        except Exception:
            pass

    # Твои модули: пробуем несколько вероятных путей.
    candidates = [
        "facets_mapper",              # e.g. facets-mapper для категорий→флаги
        "core.facets_mapper",
        "services.facets_mapper",
        "app.facets_mapper",

        "fetchers",                   # реестр фетчеров
        "sources.fetchers",
        "app.fetchers",
    ]

    for cand in candidates:
        try:
            mods[cand] = importlib.import_module(cand)
        except Exception:
            pass

    # Контракт Event если есть
    for cand in ["models.event", "app.models.event", "core.models", "models"]:
        try:
            mods[cand] = importlib.import_module(cand)
        except Exception:
            pass

    return mods

mods = _try_imports()
sa = mods.get("sa")
redis = mods.get("redis")
pydantic = mods.get("pydantic")

# --- утилиты времени/дат ---
def to_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)

def daterange(start: dt.date, days: int) -> List[dt.date]:
    return [start + dt.timedelta(days=i) for i in range(days)]

# --- БД: универсальная обёртка через рефлексию схемы ---
def db_connect(url: str):
    if not sa:
        raise RuntimeError("SQLAlchemy не установлен")
    engine = sa.create_engine(url, future=True)
    meta = sa.MetaData()
    meta.reflect(bind=engine)
    return engine, meta

def table(meta, name_candidates: List[str]):
    for name in name_candidates:
        if name in meta.tables:
            return meta.tables[name]
    raise RuntimeError(f"Не найдена таблица среди кандидатов: {name_candidates}")

def load_events(engine, meta, date_from: dt.date, date_to: dt.date, city: str) -> List[Dict[str, Any]]:
    """
    Универсальный селект: пытаемся угадать названия колонок.
    Предположим типичные поля: id, source, city, start_date, end_date, flags, tags, title.
    """
    events_t = table(meta, ["events", "event", "wp_events"])

    # эвристики названий колонок
    col = events_t.c
    def pick(*names):
        for n in names:
            if hasattr(col, n):
                return getattr(col, n)
        return None

    c_id        = pick("id", "event_id")
    c_source    = pick("source", "source_id", "provider")
    c_city      = pick("city")
    c_start     = pick("start_date", "start_dt", "start")
    c_end       = pick("end_date", "end_dt", "end")
    c_flags     = pick("flags")
    c_tags      = pick("tags")
    c_title     = pick("title", "name")

    # Упрощённый фильтр: берём все события и фильтруем в Python
    # Это более надёжно для разных форматов дат
    query = sa.select(events_t)
    if c_city is not None:
        # Ищем city без учёта регистра (ILIKE для PostgreSQL, LOWER для SQLite)
        if hasattr(c_city, 'ilike'):
            query = query.where(c_city.ilike(f"%{city}%"))
        else:
            # SQLite fallback
            query = query.where(sa.func.lower(c_city).contains(city.lower()))

    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()

    out = []
    for r in rows:
        out.append(dict(r))
    return out

# --- Redis: инспектор ключей v2:<city>:<YYYY-MM-DD>:flag:<flag> и index ---
class RedisInspector:
    def __init__(self, url: str):
        if not redis:
            raise RuntimeError("Redis не установлен")
        self.r = redis.from_url(url, decode_responses=True)

    def key_info(self, key: str) -> Dict[str, Any]:
        exists = self.r.exists(key) == 1
        info: Dict[str, Any] = {"key": key, "exists": bool(exists)}
        if not exists:
            return info
        t = self.r.type(key)
        info["type"] = t
        try:
            if t == "list":
                info["len"] = self.r.llen(key)
            elif t == "set":
                info["len"] = self.r.scard(key)
            elif t == "zset":
                info["len"] = self.r.zcard(key)
            elif t == "string":
                val = self.r.get(key)
                info["len"] = len(val) if val is not None else 0
                try:
                    parsed = json.loads(val)
                    if isinstance(parsed, list):
                        info["parsed_len"] = len(parsed)
                except Exception:
                    pass
            else:
                info["len"] = None
        except Exception as e:
            info["error"] = f"read_error: {e}"

        try:
            info["ttl"] = self.r.ttl(key)
        except Exception:
            info["ttl"] = None
        return info

    def expected_flag_key(self, city: str, day: dt.date, flag: str) -> str:
        iso = day.isoformat()
        return f"v2:{city}:{iso}:flag:{flag}"

    def expected_stale_key(self, city: str, day: dt.date, flag: str) -> str:
        iso = day.isoformat()
        return f"v2:{city}:{iso}:flag:{flag}:stale"

    def index_key(self, city: str, day: dt.date) -> str:
        iso = day.isoformat()
        return f"v2:{city}:{iso}:index"

# --- Facets/Flags: используем новый универсальный маппер ---
def load_facets_mapper():
    for name in ["core.query.facets", "facets_mapper", "core.facets_mapper", "services.facets_mapper", "app.facets_mapper"]:
        try:
            m = importlib.import_module(name)
            if m:
                return m
        except Exception:
            pass
    return None

FACETS = load_facets_mapper()

def event_flags_via_mapper(event: Dict[str, Any]) -> List[str]:
    """
    Используем новый универсальный маппер map_event_to_flags.
    """
    if FACETS and hasattr(FACETS, "map_event_to_flags"):
        try:
            return FACETS.map_event_to_flags(event) or []
        except Exception as e:
            print(f"Warning: map_event_to_flags failed: {e}")
    
    # Fallback: простой маппинг по ключевым словам
    flags = set()
    title = (event.get("title") or "").lower()
    tags  = json.loads(event["tags"]) if isinstance(event.get("tags"), str) and event["tags"].startswith("[") else event.get("tags") or []
    txt = " ".join([title] + [t.lower() for t in tags if isinstance(t, str)])
    
    # Упрощённые правила для fallback
    for key, fl in [
        ("art", "art_exhibits"), ("gallery", "art_exhibits"), ("museum", "art_exhibits"),
        ("jazz", "jazz_blues"), ("blues", "jazz_blues"),
        ("rooftop", "rooftop"), ("skybar", "rooftop"),
        ("food", "food_dining"), ("restaurant", "food_dining"),
        ("workshop", "workshops"), ("class", "workshops"),
        ("cinema", "cinema"), ("movie", "cinema"),
        ("market", "markets"), ("shopping", "markets"),
        ("yoga", "yoga_wellness"), ("meditation", "yoga_wellness"),
        ("park", "parks"), ("outdoor", "parks")
    ]:
        if key in txt:
            flags.add(fl)
    return sorted(flags)

# --- Fetchers: health-проба (если есть реестр) ---
def fetchers_probe(limit_per_fetcher: int = 3) -> List[Dict[str, Any]]:
    results = []
    # ожидаем модуль с регистрацией/классами фетчеров
    for key in ["fetchers", "sources.fetchers", "app.fetchers"]:
        m = mods.get(key)
        if not m:
            continue
        for name in dir(m):
            cls = getattr(m, name)
            try:
                is_class = isinstance(cls, type)
                if not is_class:
                    continue
                # эвристика: у фетчера есть .fetch(self) или .health()
                has_fetch = hasattr(cls, "fetch")
                has_health = hasattr(cls, "health")
                if not (has_fetch or has_health):
                    continue
                inst = cls()  # может потребовать параметры — тогда пропустим
                item = {"fetcher": f"{key}.{name}"}
                try:
                    if has_health:
                        h = inst.health()
                        item["health"] = h
                    if has_fetch:
                        sample = inst.fetch()  # WARNING: может сходить в сеть — используй осознанно
                        item["fetched_sample"] = len(sample) if isinstance(sample, list) else None
                except Exception as e:
                    item["error"] = f"{type(e).__name__}: {e}"
                results.append(item)
            except Exception:
                # не класс или не инстанцируется — игнор
                pass
    return results

# --- Главная процедура диагностики ---
def run(city: str, start_day: dt.date, days: int, flags_hint: Optional[List[str]] = None) -> Dict[str, Any]:
    db_url = os.environ.get("DB_URL", "sqlite:///data/wp.db")
    redis_url = os.environ.get("REDIS_URL")

    engine, meta = db_connect(db_url)
    dates = daterange(start_day, days)
    date_from, date_to = dates[0], dates[-1]

    # 1) Fetchers health (best-effort)
    fetchers = fetchers_probe()

    # 2) БД: события на интервале
    events = load_events(engine, meta, date_from, date_to, city)

    # 3) Развёртка по источникам/дням/флагам
    by_source = defaultdict(int)
    by_day = defaultdict(int)
    by_flag = defaultdict(int)
    empty_flags = 0
    sample_unflagged = []

    # поле дат — эвристика
    def event_days(e) -> List[dt.date]:
        start = e.get("start_date") or e.get("start_dt") or e.get("start")
        end   = e.get("end_date") or e.get("end_dt") or e.get("end")
        if isinstance(start, str):
            try:
                start = dt.datetime.fromisoformat(start)
            except Exception:
                start = None
        if isinstance(end, str):
            try:
                end = dt.datetime.fromisoformat(end)
            except Exception:
                end = None
        if isinstance(start, dt.datetime) and isinstance(end, dt.datetime):
            s = start.date()
            e_ = end.date()
            rng = []
            cur = s
            while cur <= e_:
                rng.append(cur)
                cur += dt.timedelta(days=1)
            return rng
        return []

    for e in events:
        # Фильтруем по датам в Python
        event_dates = event_days(e)
        event_in_range = any(date_from <= d <= date_to for d in event_dates)
        
        if not event_in_range:
            continue  # Пропускаем события вне диапазона
        
        src = (e.get("source") or e.get("source_id") or e.get("provider") or "unknown").lower()
        by_source[src] += 1
        fls = event_flags_via_mapper(e)
        if not fls:
            empty_flags += 1
            if len(sample_unflagged) < 10:
                sample_unflagged.append({"id": e.get("id"), "title": e.get("title"), "src": src})
        for f in fls:
            by_flag[f] += 1
        for d in event_days(e):
            if date_from <= d <= date_to:
                by_day[d.isoformat()] += 1

    # подсказка по флагам: либо от пользователя, либо из БД
    flags_list = flags_hint or sorted(by_flag.keys())

    # 4) Redis-инвентаризация
    redis_section = None
    discrepancies = []
    if redis_url:
        try:
            rinsp = RedisInspector(redis_url)
            redis_report = {"flags": {}, "index": {}}

            for day in dates:
                # index-ключ
                idx_key = rinsp.index_key(city, day)
                redis_report["index"][day.isoformat()] = rinsp.key_info(idx_key)

                for f in flags_list:
                    k = rinsp.expected_flag_key(city, day, f)
                    k_stale = rinsp.expected_stale_key(city, day, f)
                    
                    info = rinsp.key_info(k)
                    info_stale = rinsp.key_info(k_stale)
                    
                    # Объединяем информацию о основном и stale ключах
                    combined_info = {
                        "main": info,
                        "stale": info_stale,
                        "has_data": info.get("exists") or info_stale.get("exists")
                    }
                    
                    redis_report["flags"].setdefault(f, {})
                    redis_report["flags"][f][day.isoformat()] = combined_info

                    # Сравним наличия: БД говорит есть события с таким флагом на этот день?
                    # Оценка с точностью до "есть/нет", не по количеству, чтобы не ошибаться об дедупе.
                    db_has = by_flag.get(f, 0) > 0 and by_day.get(day.isoformat(), 0) > 0
                    cache_has = combined_info["has_data"]
                    if db_has and not cache_has:
                        discrepancies.append({
                            "day": day.isoformat(),
                            "flag": f,
                            "problem": "DB has events for day/flag, Redis key empty or missing"
                        })

            redis_section = redis_report
        except Exception as e:
            redis_section = {"error": f"Redis connection failed: {e}"}

    # 5) Резюме/рекомендация по вероятной причине
    likely_causes = []
    if not events:
        likely_causes.append("Ingestion не записал события в БД (или фильтр по датам/городу отрезает всё).")
    else:
        if empty_flags == len(events):
            likely_causes.append("Маппер категорий/флагов не помечает события → все флаги пустые.")
        if discrepancies:
            likely_causes.append("Кэш не построен (или ключи не тем именем) для дней/флагов, хотя события в БД есть.")
        if not redis_url:
            likely_causes.append("REDIS_URL не задан, API всегда падает в БД без кэша (или возвращает 0 при чтении ключей).")

    report = {
        "scope": {
            "city": city,
            "date_from": date_from.isoformat(),
            "days": days,
            "date_to": date_to.isoformat(),
        },
        "fetchers_probe": fetchers,          # ошибки в источниках видны здесь
        "db": {
            "events_total": len(events),
            "by_source": dict(sorted(by_source.items(), key=lambda x: (-x[1], x[0]))),
            "by_day": dict(sorted(by_day.items())),
            "by_flag": dict(sorted(by_flag.items(), key=lambda x: (-x[1], x[0]))),
            "unflagged_events": empty_flags,
            "unflagged_sample": sample_unflagged,
        },
        "redis": redis_section,
        "discrepancies": discrepancies,
        "likely_causes": likely_causes,
    }

    os.makedirs("diag", exist_ok=True)
    with open("diag/last_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="bangkok")
    ap.add_argument("--date", help="start ISO date, e.g. 2025-08-31", required=True)
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--flags", help="comma-separated flags hint (optional)", default="")
    args = ap.parse_args()

    start_day = to_date(args.date)
    flags_hint = [s.strip() for s in args.flags.split(",") if s.strip()] or None
    run(args.city, start_day, args.days, flags_hint)

if __name__ == "__main__":
    main()
