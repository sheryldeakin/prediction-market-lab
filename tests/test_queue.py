import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import run_queue


class FakeProc:
    def __init__(self, pid, ppid, name, cmdline):
        self.pid = pid
        self.info = {"name": name, "ppid": ppid, "cmdline": cmdline}


def test_own_jobs_counts_each_job_once_and_ignores_other_programs(monkeypatch):
    procs = [
        FakeProc(10, 1, "python.exe", ["python", "-m", "models.btc_15m.meta"]),          # launcher
        FakeProc(11, 10, "python.exe", ["python", "-m", "models.btc_15m.meta"]),         # its child
        FakeProc(20, 1, "python.exe", ["python", "-m", "models.btc_15m.drift"]),
        FakeProc(30, 1, "chrome.exe", ["chrome"]),
        FakeProc(40, 1, "python.exe", ["python", "other_script.py"]),
    ]
    monkeypatch.setattr(run_queue.psutil, "process_iter", lambda attrs: procs)
    jobs = run_queue.own_jobs()
    assert sorted(jobs) == ["models.btc_15m.drift", "models.btc_15m.meta"]
