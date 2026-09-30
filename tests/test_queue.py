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
        FakeProc(50, 1, "python.exe", ["python", "scripts/run_queue.py", "python -m models.btc_15m.rules"]),   # the queue itself
    ]
    monkeypatch.setattr(run_queue.psutil, "process_iter", lambda attrs: procs)
    jobs = run_queue.own_jobs()
    assert sorted(jobs) == ["models.btc_15m.drift", "models.btc_15m.meta"]


def test_room_quiet_profile_refuses_when_machine_is_busy(monkeypatch):
    monkeypatch.setattr(run_queue, "own_jobs", lambda: [])
    monkeypatch.setattr(run_queue.psutil, "cpu_percent", lambda interval=None: 90.0)
    class VM: available = 30e9
    monkeypatch.setattr(run_queue.psutil, "virtual_memory", lambda: VM)
    monkeypatch.setattr(run_queue, "gpu", lambda: (10.0, 2.0, 32.0))
    ok, _ = run_queue.room("quiet", 2)
    assert not ok                                    # idle cpu 10% < 25%
    assert run_queue.room("full", 2)[0]              # full profile ignores load
    monkeypatch.setattr(run_queue.psutil, "cpu_percent", lambda interval=None: 40.0)
    assert run_queue.room("quiet", 2)[0]
    monkeypatch.setattr(run_queue, "gpu", lambda: (80.0, 2.0, 32.0))
    assert not run_queue.room("quiet", 2)[0]         # gpu 80% busy


def test_room_counts_own_jobs_in_both_profiles(monkeypatch):
    monkeypatch.setattr(run_queue, "own_jobs", lambda: ["models.a", "models.b"])
    monkeypatch.setattr(run_queue.psutil, "cpu_percent", lambda interval=None: 5.0)
    class VM: available = 30e9
    monkeypatch.setattr(run_queue.psutil, "virtual_memory", lambda: VM)
    monkeypatch.setattr(run_queue, "gpu", lambda: (0.0, 0.0, 32.0))
    assert not run_queue.room("full", 2)[0]
    assert run_queue.room("full", 3)[0]
