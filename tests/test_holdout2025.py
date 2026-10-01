import json
import sys

import pandas as pd
import pytest

import models.btc_15m.holdout2025 as H


def test_the_holdout_refuses_a_second_run(tmp_path, monkeypatch):
    stamp = tmp_path / "holdout_2025.json"
    stamp.write_text(json.dumps({"ran_at": "2026-10-01 00:00 UTC"}))
    monkeypatch.setattr(H, "STAMP", stamp)
    monkeypatch.setattr(sys, "argv", ["holdout2025"])
    with pytest.raises(SystemExit) as e:
        H.main()
    assert "scored once already" in str(e.value)


def test_bit_rates_are_the_training_up_rates_after_each_previous_direction():
    D = pd.DataFrame({"prev_up": [1, 1, 1, 0, 0], "y": [0, 0, 1, 1, 1]})
    assert H.bit_rates(D) == {0: 1.0, 1: pytest.approx(1 / 3)}
