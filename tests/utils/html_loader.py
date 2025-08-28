from pathlib import Path


def load_html(relative: str) -> str:
    """Return the HTML string for a fixture file."""
    base = Path(__file__).resolve().parent.parent / "fixtures" / "html"
    return (base / relative).read_text(encoding="utf-8")
