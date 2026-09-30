"""Daily runner for the forward log: extends predictions.csv, redraws the charts and
re-splices the README tables. Meant for a scheduler running pythonw.exe (no console),
so all output goes to logs/forward_log.txt. Commits nothing; review and push by hand.

    .venv\\Scripts\\pythonw.exe scripts\\run_forward_log.py
"""
import datetime as dt
import os
import runpy
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
(ROOT / "logs").mkdir(exist_ok=True)
log = open(ROOT / "logs" / "forward_log.txt", "a")
sys.stdout = sys.stderr = log
print(f"\n=== {dt.datetime.utcnow():%Y-%m-%d %H:%M} UTC ===")
try:
    for mod in ("models.btc_15m.log", "models.btc_15m.charts"):
        sys.argv = [mod]
        runpy.run_module(mod, run_name="__main__")
    from models.btc_15m.publish import load_env
    load_env()
    if os.environ.get("MONGODB_URI"):
        sys.argv = ["models.btc_15m.publish"]
        runpy.run_module("models.btc_15m.publish", run_name="__main__")
    else:
        print("MONGODB_URI not set; database publish skipped")
    sys.argv = ["update_readme"]
    runpy.run_path(str(ROOT / "scripts" / "update_readme.py"), run_name="__main__")
    print("ok")
except Exception:
    traceback.print_exc()
finally:
    log.close()
