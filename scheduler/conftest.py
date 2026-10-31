"""Make `app` (this package) and `adapters` (repo root) importable regardless of
whether pytest is invoked from the repo root (`python -m pytest scheduler/tests`, as
CI does) or from `scheduler/` directly (`cd scheduler && python -m pytest tests`).
"""
import sys
from pathlib import Path

_SCHEDULER_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCHEDULER_DIR.parent

for _p in (str(_REPO_ROOT), str(_SCHEDULER_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
