"""Make `app` (this package) and `adapters` (repo root) importable regardless of
whether pytest is invoked from the repo root (`python -m pytest api/tests`, as CI
does) or from `api/` directly (`cd api && python -m pytest tests`).
"""
import sys
from pathlib import Path

_API_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _API_DIR.parent

for _p in (str(_REPO_ROOT), str(_API_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
