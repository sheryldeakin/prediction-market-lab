"""Wait for one queue to finish, then start another, without a terminal attached.

The first queue is finished when the last line of its log is a "done" line and none of
this repo's experiment processes is running (checked twice, a minute apart).

    python scripts/run_after_queue.py <log of the running queue> -- <run_queue.py arguments>
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from run_queue import own_jobs  # noqa: E402

log, args = Path(sys.argv[1]), sys.argv[sys.argv.index("--") + 1:]
idle = 0
while idle < 2:
    lines = log.read_text(errors="ignore").strip().splitlines() if log.exists() else []
    tail = lines[-1] if lines else ""
    finished = tail[:8].replace(":", "").isdigit() and " done " in tail and not own_jobs()
    idle = idle + 1 if finished else 0
    time.sleep(60)
py = str(ROOT / ".venv" / "Scripts" / "python.exe")
subprocess.run([py, str(ROOT / "scripts" / "run_queue.py"), *args], cwd=ROOT)
