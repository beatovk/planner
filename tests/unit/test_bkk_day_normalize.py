from core.utils.dates import normalize_bkk_day

def test_normalize_bkk_day_plain():
    assert normalize_bkk_day("2025-08-31") == "2025-08-31"

def test_normalize_bkk_day_iso_utc_to_bkk():
    # 2025-08-31T22:30:00Z -> в BKK это уже 2025-09-01
    assert normalize_bkk_day("2025-08-31T22:30:00Z") == "2025-09-01"
