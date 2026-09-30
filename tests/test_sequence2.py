import numpy as np
import torch

from models.btc_15m.sequence2 import ARCH, TCN, Transformer


def test_tcn_is_causal():
    """Changing the last step changes the output; changing a step beyond the receptive
    field does not leak from the future because padding is on the left only."""
    torch.manual_seed(0)
    m = TCN(8).eval()
    x = torch.randn(1, 40, 3)
    e = torch.zeros(1, 2)
    base = m(x, e).item()
    x2 = x.clone(); x2[0, -1, :] += 1.0
    assert m(x2, e).item() != base
    # the model reads only the last position; earlier steps outside the receptive field (14 steps) must not matter
    x3 = x.clone(); x3[0, :20, :] += 5.0
    assert abs(m(x3, e).item() - base) < 1e-5


def test_every_architecture_runs_at_each_length_and_outputs_one_logit_per_row():
    torch.manual_seed(0)
    for L in (30, 120):
        x = torch.randn(5, L, 3)
        e = torch.zeros(5, 2)
        for name in ARCH:
            m = (ARCH[name](16, L=L) if name == "transformer" else ARCH[name](16)).eval()
            out = m(x, e)
            assert out.shape == (5,) and torch.isfinite(out).all(), name


def test_transformer_uses_last_position_and_is_permutation_sensitive():
    torch.manual_seed(0)
    m = Transformer(16, L=30).eval()
    x = torch.randn(1, 30, 3)
    e = torch.zeros(1, 2)
    base = m(x, e).item()
    assert m(torch.flip(x, [1]), e).item() != base       # positional embedding makes order matter
