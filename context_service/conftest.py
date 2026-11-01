"""Make `app` (this package) importable regardless of invocation directory.

Mirrors the pattern in api/conftest.py.
"""
import sys
from pathlib import Path

_CS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _CS_DIR.parent

for _p in (str(_REPO_ROOT), str(_CS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
