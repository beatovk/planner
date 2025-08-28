# Tests

## HTML fixtures

Placeholder HTML pages are stored under `tests/fixtures/html`.
To refresh them with real pages:

1. Open the desired page in a browser.
2. Save the HTML (`Ctrl+S`) without external assets.
3. Place the file as `tests/fixtures/html/<source>/pageN.html`.

Do not commit private or sensitive data.

## Snapshots

Event counts are stored as plain integers in `tests/fixtures/snapshots/*.txt`.
If parser changes lead to different counts, update the corresponding file.

## Running tests

Offline tests can be executed with:

```
pytest
```

Network tests (marked with `@pytest.mark.network`) are skipped by default.
Run them explicitly via:

```
pytest -m network
```
