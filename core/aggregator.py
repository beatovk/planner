from __future__ import annotations
import os
from typing import List
from core.fetchers import BKMagazineFetcher, DatabaseFetcher, ZipeventFetcher
from core.events import Event
from core.dedup import merge_events
from core.quality.qa import quality_report, print_quality_console, write_quality_json
from storage.db import Database


# Функция загрузки seed URL отключена - нет реальных данных
# def _load_zipevent_seeds() -> List[str]:
#     """Load seed URLs for ZipeventFetcher from config file."""
#     seeds = []
#     config_path = "config/zipevent_seeds.txt"
#     
#     try:
#         if os.path.exists(config_path):
#             with open(config_path, "r", encoding="utf-8") as f:
#                 for line in f:
#                     line = line.strip()
#                     if line and not line.startswith("#"):
#                         seeds.append(line)
#             print(f"[config] Loaded {len(seeds)} seed URLs from {config_path}")
#         else:
#             print(f"[config] Seed file not found: {config_path}")
#     except Exception as e:
#         print(f"[config] Error loading seeds: {e}")
#     
#     return seeds


def collect_events() -> List[Event]:
    fetchers = [
        BKMagazineFetcher(), 
        # DatabaseFetcher(),  # Отключен - нет реальных данных
        # ZipeventFetcher(seeds=zipevent_seeds)  # Отключен - нет реальных seed URL
    ]
    events: List[Event] = []
    for fetcher in fetchers:
        events.extend(fetcher.fetch())
    # дедуп и слияние полей
    before = len(events)
    merged = merge_events(events)
    after = len(merged)
    print(f"[dedup] input={before} -> merged={after} (Δ={before-after})")
    report = quality_report(list(merged))
    print_quality_console(report)
    out_path = os.environ.get("QA_JSON_OUT")
    if out_path:
        write_quality_json(report, out_path)
    # optional DB persist (controlled by DB_URL env)
    db_url = os.environ.get("DB_URL")
    if db_url:
        try:
            db = Database(db_url)
            db.create_tables()
            written = db.upsert_events(merged, city=os.environ.get("CITY", "bangkok"))
            print(f"[db] upsert_events wrote={written} rows to {db_url}")
        except Exception as exc:
            print(f"[db] ERROR: {exc}")
    return merged
