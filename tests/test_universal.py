from pathlib import Path

from core.fetchers.bk_magazine import BKMagazineFetcher
from core.fetchers.timeout_bkk import TimeOutBKKFetcher
from core.fetchers.validator import ensure_events
from tests.utils.html_loader import load_html

SNAPSHOT_DIR = Path(__file__).resolve().parent / "fixtures" / "snapshots"


def _expected(name: str) -> int:
    return int((SNAPSHOT_DIR / name).read_text().strip())


def _parse(fetcher_cls, folder: str):
    fetcher = fetcher_cls()
    raw = []

    # Для TimeOut Bangkok используем реальную страницу
    if folder == "timeout_bkk":
        try:
            html_path = (
                Path(__file__).resolve().parent
                / "fixtures"
                / "html"
                / "real"
                / "timeout_bkk_events.html"
            )
            if html_path.exists():
                html_content = html_path.read_text(encoding="utf-8")
                raw = fetcher._parse_page(html_content)
            else:
                # Fallback к старым фикстурам
                for page in range(1, 4):
                    html = load_html(f"{folder}/page{page}.html")
                    raw.extend(fetcher._parse_page(html))
        except Exception:
            # Fallback к старым фикстурам
            for page in range(1, 4):
                html = load_html(f"{folder}/page{page}.html")
                raw.extend(fetcher._parse_page(html))
    else:
        # Для других фетчеров используем старые фикстуры
        for page in range(1, 4):
            html = load_html(f"{folder}/page{page}.html")
            raw.extend(fetcher._parse_page(html))

    return ensure_events(raw, source_name=fetcher.name)


def test_universal_aggregator():
    timeout_events = _parse(TimeOutBKKFetcher, "timeout_bkk")
    bk_events = _parse(BKMagazineFetcher, "bk_magazine")
    combined = timeout_events + bk_events
    unique = {e.identity_key(): e for e in combined}
    assert len(unique) == _expected("universal_count.txt")
