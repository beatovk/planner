from __future__ import annotations

import json
import os
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from ..logging import logger
from ..events import Event
from .dup import find_duplicates


def _pct(part: int, total: int) -> float:
    return round((part / total) * 100, 2) if total else 0.0


def quality_report(events: List[Event]) -> Dict[str, Any]:
    """Return quality metrics for the provided events."""
    total = len(events)
    report: Dict[str, Any] = {"total": total}
    if total == 0:
        return report

    start_filled = sum(1 for e in events if e.start)
    end_filled = sum(1 for e in events if e.end)
    check_images = os.getenv("QA_CHECK_IMAGES", "false").lower() == "true"
    images = [str(e.image) for e in events if e.image]

    valid_by_url: Dict[str, bool] = {}
    if check_images and images:
        # ленивый импорт requests (чтобы модуль работал без него)
        try:
            import requests  # type: ignore
        except Exception:
            logger.warning("QA_CHECK_IMAGES=true, но 'requests' не установлен — считаем только наличие image.")
            check_images = False

    if check_images and images:
        timeout = float(os.getenv("QA_IMG_TIMEOUT", "4.0"))
        workers = max(1, int(os.getenv("QA_IMG_WORKERS", "8")))

        def _check(url: str) -> bool:
            try:
                # 1) HEAD
                resp = requests.head(url, timeout=timeout)  # type: ignore[name-defined]
                if resp.status_code < 400:
                    return True
                # 2) Fallback GET — некоторые бэкенды блокируют HEAD
                resp = requests.get(url, timeout=timeout, stream=True)  # type: ignore[name-defined]
                return resp.status_code < 400
            except Exception:
                return False

        with ThreadPoolExecutor(max_workers=min(workers, len(images))) as ex:
            futures = {ex.submit(_check, u): u for u in images}
            for fut in as_completed(futures):
                url = futures[fut]
                try:
                    valid_by_url[url] = bool(fut.result())
                except Exception:
                    valid_by_url[url] = False

        valid_count = sum(1 for ok in valid_by_url.values() if ok)
        image_pct = _pct(valid_count, total)
    else:
        image_pct = _pct(len(images), total)

    desc_lengths = [len(e.desc) for e in events if e.desc]
    avg_desc_len = round(statistics.mean(desc_lengths), 2) if desc_lengths else 0.0
    median_desc_len = statistics.median(desc_lengths) if desc_lengths else 0.0

    dup_groups, fuzzy_groups = find_duplicates(events)
    duplicate_events = sum(len(g) - 1 for g in dup_groups)
    duplicates_pct = _pct(duplicate_events, total)

    per_source: Dict[str, Dict[str, Any]] = {}
    for src in {e.source for e in events}:
        subset = [e for e in events if e.source == src]
        per_source[src] = {
            "count": len(subset),
            "filled_start_pct": _pct(sum(1 for e in subset if e.start), len(subset)),
            "filled_end_pct": _pct(sum(1 for e in subset if e.end), len(subset)),
            # если проверяем доступность, учитываем только валидные ссылки
            "image_pct": (
                _pct(sum(1 for e in subset if e.image and valid_by_url.get(str(e.image), False)), len(subset))
                if check_images
                else _pct(sum(1 for e in subset if e.image), len(subset))
            ),
        }

    report.update(
        {
            "filled_start_pct": _pct(start_filled, total),
            "filled_end_pct": _pct(end_filled, total),
            "image_pct": image_pct,
            "avg_desc_len": avg_desc_len,
            "median_desc_len": median_desc_len,
            "duplicates_pct": duplicates_pct,
            "duplicates": [[e.id for e in g] for g in dup_groups],
            "fuzzy_duplicates": [[a.id, b.id] for a, b in fuzzy_groups],
            "per_source": per_source,
        }
    )
    return report


def print_quality_console(report: Dict[str, Any]) -> None:
    """Print a short console report."""
    print("QA REPORT")
    for key in [
        "total",
        "filled_start_pct",
        "filled_end_pct",
        "image_pct",
        "avg_desc_len",
        "median_desc_len",
        "duplicates_pct",
    ]:
        if key in report:
            print(f" - {key}: {report[key]}")
    if report.get("per_source"):
        print("Per source:")
        for src, stats in report["per_source"].items():
            print(f"   {src}: {stats}")


def write_quality_json(report: Dict[str, Any], path: str = "qa_report.json") -> None:
    """Persist metrics to a JSON file."""
    # создаём директорию, если надо
    dir_ = os.path.dirname(path)
    if dir_:
        os.makedirs(dir_, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
