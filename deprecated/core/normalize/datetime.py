from __future__ import annotations
import calendar
import re
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
import dateparser

SETTINGS = {
    "TIMEZONE": "Asia/Bangkok",
    "TO_TIMEZONE": "Asia/Bangkok",
    "RETURN_AS_TIMEZONE_AWARE": True,
    "PREFER_DAY_OF_MONTH": "first",
}
LANGUAGES = ["en", "th"]
TZ = ZoneInfo(SETTINGS["TIMEZONE"])

def _at_start_of_day(dt: datetime) -> datetime:
    return dt.astimezone(TZ).replace(hour=0, minute=0, second=0, microsecond=0)

def _at_end_of_day(dt: datetime) -> datetime:
    return dt.astimezone(TZ).replace(hour=23, minute=59, second=59, microsecond=0)

def parse_date(value: str | None, *, base_dt: datetime | None = None) -> datetime | None:
    if not value:
        return None
    settings = SETTINGS.copy()
    if base_dt:
        # гарантируем TZ-aware базу
        settings["RELATIVE_BASE"] = base_dt if base_dt.tzinfo else base_dt.replace(tzinfo=TZ)
    return dateparser.parse(value, languages=LANGUAGES, settings=settings)

def parse_range(text: str) -> tuple[datetime | None, datetime | None]:
    if not text:
        return None, None

    now = datetime.now(TZ)
    text_low = text.strip().lower()

    # 1) «4–6 Jan» И «Jan 4–6»
    m1 = re.match(r"(\d{1,2})\s*[–\-]\s*(\d{1,2})\s*([a-z]+)", text_low)
    m2 = re.match(r"([a-z]+)\s+(\d{1,2})\s*[–\-]\s*(\d{1,2})", text_low)
    if m1 or m2:
        if m1:
            start_day, end_day, month = m1.groups()
        else:
            month, start_day, end_day = m2.groups()
        year = now.year
        start = parse_date(f"{start_day} {month} {year}")
        end = parse_date(f"{end_day} {month} {year}")
        # нормализуем к началу/концу дня
        return (_at_start_of_day(start) if start else None,
                _at_start_of_day(end) if end else None)

    if (
        "до конца месяца" in text_low
        or "end of month" in text_low
        or "end of the month" in text_low
        or "สิ้นเดือน" in text_low
    ):
        start = _at_start_of_day(now)
        last_day = calendar.monthrange(now.year, now.month)[1]
        end = _at_end_of_day(datetime(now.year, now.month, last_day, tzinfo=TZ))
        return start, end

    if (
        ("кажд" in text_low and "пятниц" in text_low)
        or "every friday" in text_low
        or "ทุกวันศุกร์" in text_low
    ):
        days_ahead = (4 - now.weekday()) % 7
        start = _at_start_of_day(now) + timedelta(days=days_ahead)
        end = _at_end_of_day(start)
        return start, end

    single = parse_date(text)
    if single:
        return _at_start_of_day(single), _at_start_of_day(single)
    return None, None

def normalize_start_end(
    raw_start: str | None,
    raw_end: str | None,
    time_str: str | None,
) -> tuple[datetime | None, datetime | None, str | None]:
    start = parse_date(raw_start) if raw_start else None
    end = parse_date(raw_end) if raw_end else None

    if start is None and end is None and time_str:
        start, end = parse_range(time_str)

    if start and not end:
        end = start
    if end and not start:
        start = end

    return start, end, time_str
