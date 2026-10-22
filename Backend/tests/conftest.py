import os
from pathlib import Path

_TEST_DB = (Path(__file__).resolve().parent.parent / "test.db").resolve()

# These must be set before `app` is imported anywhere, because the settings
# object is constructed at import time. pytest imports conftest.py before
# collecting test modules, so this is the earliest reliable hook.
os.environ["SENTINEL_DATABASE_URL"] = f"sqlite:///{_TEST_DB.as_posix()}"
os.environ["SENTINEL_NVD_ENABLED"] = "false"
os.environ["SENTINEL_NVD_MIN_INTERVAL_SECONDS"] = "0"
os.environ["SENTINEL_LLM_PROVIDER"] = "none"
os.environ["SENTINEL_OPENROUTER_API_KEY"] = ""
os.environ["SENTINEL_OPENAI_API_KEY"] = ""

# Start each run from a clean database so counts are deterministic.
_TEST_DB.unlink(missing_ok=True)