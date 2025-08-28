# Back-compat wrapper for tests that import `main:app`
import warnings
warnings.warn("main.py is deprecated; use apps.api.main", DeprecationWarning)

from apps.api.main import app  # noqa: F401
