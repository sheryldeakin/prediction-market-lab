"""Wait for one queue to finish, then start another. Used once on 2026-10-01 to chain the
regeneration queue into the new-studies queue without a terminal attached.

    python scripts/run_after_queue.py <log of the running queue> -- <run_queue.py arguments>
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
log, args = Path(sys.argv[1]), sys.argv[sys.argv.index("--") + 1:]
while True:
    tail = log.read_text(errors="ignore").strip().splitlines()[-1] if log.exists() else ""
    if tail.startswith(tuple("0123456789")) and " done " in tail and "charts" in tail:
        break
    time.sleep(60)
py = str(ROOT / ".venv" / "Scripts" / "python.exe")
subprocess.run([py, str(ROOT / "scripts" / "run_queue.py"), *args], cwd=ROOT)
