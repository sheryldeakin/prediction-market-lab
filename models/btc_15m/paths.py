"""Where the raw data lives. Defaults to ./data; the environment variable LAB_DATA_ROOT points
every raw-data reader at another directory, so a second checkout can read the first one's
downloads without copying them. Derived caches that a study writes (features.CACHE_DIR, the
mechanism study's event tables) stay under the working copy's own ./data on purpose: pointing
LAB_DATA_ROOT at a shared directory makes the readers read from it, never the writers write
into it.
"""
from __future__ import annotations

import os
from pathlib import Path


def data_root() -> Path:
    return Path(os.environ.get("LAB_DATA_ROOT", "data"))


DATA_ROOT = data_root()
