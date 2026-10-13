import os
from pathlib import Path

# These must be set before `app` is imported anywhere, because the settings
# object is constructed at import time. pytest imports conftest.py before
# collecting test modules, so this is the earliest reliable hook.
os.environ.setdefault("SENTINEL_DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SENTINEL_NVD_ENABLED", "false")

# Start each run from a clean database so counts are deterministic.
_TEST_DB = Path(__file__).parent.parent / "test.db"
_TEST_DB.unlink(missing_ok=True)