import numpy as np

from models.btc_15m.cells_entry import embargo_label
from tests.test_horizons import flat


def test_embargo_label_shifts_both_ends_and_marks_the_tail():
    s = flat()
    idx = np.array([300, len(s.c) - 6])
    y0 = embargo_label(s, idx, 5, 0)
    y2 = embargo_label(s, idx, 5, 2)
    assert y0[0] == float(s.c[304] >= s.o[300])
    assert y2[0] == float(s.c[306] >= s.o[302])
    assert not np.isnan(y0[1]) and np.isnan(y2[1])             # horizon 5 from idx+2 runs past the data
