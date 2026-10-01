"""Sequence models compared properly.

Three architectures over the raw minute series (return, volume ratio, taker-buy share),
each at three sequence lengths, with the lead and hour as side inputs:

  gru          one GRU layer, hidden h
  tcn          three dilated causal 1-D convolutions (dilations 1, 2, 4), hidden h
  transformer  two encoder layers, 4 heads, width h, learned positional embedding

Honest tuning: for each test month, (h, learning rate) are chosen from a small grid by
log loss on the month before the test month, using a model trained on the months
before that; the winner is refit on all earlier months and scored on the test month.
Early stopping on the last 10% of the training rows. Every result is compared with the
one-feature baseline (the previous window at the open, the lead z-score after) on the same windows.

    python -m models.btc_15m.sequence2 --start 2025-10 --end 2026-08 --minutes 0,3
"""
from __future__ import annotations

import argparse
import itertools
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score

from models.btc_15m.data import load
from models.btc_15m.evaluate import baseline_name, baseline_walk_forward
from models.btc_15m.features import HISTORY, Series, dataset
from models.btc_15m.stats import block_bootstrap_ci, paired_difference_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.set_num_threads(2)
if DEV.type == "cuda" and os.environ.get("LAB_GPU_FRACTION"):
    torch.cuda.set_per_process_memory_fraction(float(os.environ["LAB_GPU_FRACTION"]))   # quiet profile: a quarter of the card
BATCH = 128 if os.environ.get("LAB_GPU_TARGET") else 512                                # smaller batches keep utilisation down
GRID = list(itertools.product((16, 32, 64), (3e-4, 1e-3)))


class GRUNet(nn.Module):
    def __init__(self, h, n_in=3):
        super().__init__()
        self.gru = nn.GRU(n_in, h, batch_first=True)
        self.head = nn.Sequential(nn.Linear(h + 2, 32), nn.ReLU(), nn.Dropout(0.2), nn.Linear(32, 1))

    def forward(self, x, e):
        _, hn = self.gru(x)
        return self.head(torch.cat([hn[-1], e], 1)).squeeze(1)


class TCN(nn.Module):
    def __init__(self, h, n_in=3):
        super().__init__()
        layers, c = [], n_in
        for d in (1, 2, 4):
            layers += [nn.Conv1d(c, h, 3, dilation=d), nn.ReLU()]
            c = h
        self.net = nn.Sequential(*layers)
        self.pad = 2 * (1 + 2 + 4)
        self.head = nn.Sequential(nn.Linear(h + 2, 32), nn.ReLU(), nn.Dropout(0.2), nn.Linear(32, 1))

    def forward(self, x, e):
        z = nn.functional.pad(x.transpose(1, 2), (self.pad, 0))       # causal: pad on the left only
        z = self.net(z)[:, :, -1]
        return self.head(torch.cat([z, e], 1)).squeeze(1)


class Transformer(nn.Module):
    def __init__(self, h, n_in=3, L=120):
        super().__init__()
        self.inp = nn.Linear(n_in, h)
        self.pos = nn.Parameter(torch.zeros(1, L, h))
        layer = nn.TransformerEncoderLayer(h, 4, h * 2, dropout=0.1, batch_first=True)
        self.enc = nn.TransformerEncoder(layer, 2)
        self.head = nn.Sequential(nn.Linear(h + 2, 32), nn.ReLU(), nn.Dropout(0.2), nn.Linear(32, 1))

    def forward(self, x, e):
        z = self.enc(self.inp(x) + self.pos[:, -x.shape[1]:])
        return self.head(torch.cat([z[:, -1], e], 1)).squeeze(1)


ARCH = {"gru": GRUNet, "tcn": TCN, "transformer": Transformer}


def build_steps(s: Series):
    vol24 = pd.Series(s.v).rolling(1440).mean().values
    share = np.where(s.v > 0, (s.csv[1:] - s.csv[:-1]) / (2 * np.maximum(s.v, 1e-9)) + 0.5, 0.5) - 0.5
    lv = np.log((s.v + 1e-9) / (vol24 + 1e-9))
    return np.stack([s.r1 / 10.0, np.nan_to_num(lv), share * 2], axis=1).astype(np.float32)


def sequences(s: Series, steps, k: int, L: int):
    X, E, y, t = [], [], [], []
    for i in s.window_starts():
        j = i + k
        if i < HISTORY or not s.ok[i - HISTORY:i + 15].all():
            continue
        X.append(steps[j - L:j])
        lead = (s.c[j - 1] / s.o[i] - 1) * 1e4 if k else 0.0
        E.append([lead / 10.0, (s.t[i] // 3600 % 24) / 24.0])
        y.append(s.label(i))
        t.append(int(s.t[i]))
    return np.stack(X), np.array(E, dtype=np.float32), np.array(y), np.array(t)


def fit(arch, h, lr, X, E, y, L, seed=0, epochs=12):
    torch.manual_seed(seed)
    model = (ARCH[arch](h, L=L) if arch == "transformer" else ARCH[arch](h)).to(DEV)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    lossf = nn.BCEWithLogitsLoss()
    Xt, Et, yt = torch.tensor(X).to(DEV), torch.tensor(E).to(DEV), torch.tensor(y, dtype=torch.float32).to(DEV)
    cut = int(len(y) * 0.9)
    best, state, bad = 1e9, None, 0
    for _ in range(epochs):
        model.train()
        perm = torch.randperm(cut, device=DEV)
        for b in range(0, cut, BATCH):
            idx = perm[b:b + BATCH]
            opt.zero_grad()
            lossf(model(Xt[idx], Et[idx]), yt[idx]).backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            vl = lossf(model(Xt[cut:], Et[cut:]), yt[cut:]).item()
        if vl < best - 1e-4:
            best, state, bad = vl, {k_: v.clone() for k_, v in model.state_dict().items()}, 0
        else:
            bad += 1
            if bad >= 3:
                break
    model.load_state_dict(state)
    return model


def predict(model, X, E):
    model.eval()
    out = []
    with torch.no_grad():
        for b in range(0, len(X), 4096):
            out.append(torch.sigmoid(model(torch.tensor(X[b:b + 4096]).to(DEV), torch.tensor(E[b:b + 4096]).to(DEV))).cpu().numpy())
    return np.concatenate(out)


def honest_walk_forward(arch, L, X, E, y, t, log=print):
    month = pd.to_datetime(t, unit="s").to_period("M")
    months = sorted(set(month))
    pred = np.full(len(y), np.nan)
    chosen = []
    for i in range(3, len(months)):
        m, prev = months[i], months[i - 1]
        inner_tr, inner_va = np.asarray(month < prev), np.asarray(month == prev)
        best, best_cfg = 1e9, None
        for h, lr in GRID:
            mdl = fit(arch, h, lr, X[inner_tr], E[inner_tr], y[inner_tr], L)
            ll = log_loss(y[inner_va], np.clip(predict(mdl, X[inner_va], E[inner_va]), 1e-6, 1 - 1e-6))
            if ll < best:
                best, best_cfg = ll, (h, lr)
        tr, te = np.asarray(month < m), np.asarray(month == m)
        mdl = fit(arch, best_cfg[0], best_cfg[1], X[tr], E[tr], y[tr], L)
        pred[te] = predict(mdl, X[te], E[te])
        chosen.append(best_cfg)
        log(f"  {arch} L={L} {m}: h={best_cfg[0]} lr={best_cfg[1]} acc={((pred[te] > .5) == y[te]).mean()*100:.2f}%")
    return pred, chosen


def baseline(D: pd.DataFrame, k: int, t_keep):
    """The minute's one-feature baseline (evaluate.baseline_name) on the given windows."""
    bp, _, _, bt = baseline_walk_forward(D, k)
    return pd.Series(bp, index=bt).reindex(t_keep).values, baseline_name(k)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--minutes", default="0,3")
    ap.add_argument("--lengths", default="30,120,480")
    a = ap.parse_args()
    s = Series(load(a.start, a.end))
    steps = build_steps(s)
    rows = []
    for k in [int(x) for x in a.minutes.split(",")]:
        D = dataset(s, k)
        for L in [int(x) for x in a.lengths.split(",")]:
            X, E, y, t = sequences(s, steps, k, L)
            bp, bname = baseline(D, k, t)
            for arch in ("gru", "tcn", "transformer"):
                pred, chosen = honest_walk_forward(arch, L, X, E, y, t, log=lambda x: print(x, flush=True))
                keep = ~np.isnan(pred) & ~np.isnan(bp)
                hits = ((pred[keep] > 0.5) == y[keep]).astype(float)
                bh = ((bp[keep] > 0.5) == y[keep]).astype(float)
                m_, lo, hi = block_bootstrap_ci(hits, t[keep])
                d, dlo, dhi = paired_difference_ci(hits, bh, t[keep])
                hs = ",".join(str(h) for h, _ in chosen)
                rows.append([k, arch, L, int(keep.sum()), f"{m_*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", f"{roc_auc_score(y[keep], pred[keep]):.3f}",
                             f"{log_loss(y[keep], np.clip(pred[keep], 1e-6, 1-1e-6)):.4f}", f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}] vs {bname}", hs])
                print(rows[-1], flush=True)
    with open(OUT / "sequence2.md", "w") as f:
        f.write("Sequence models with honest tuning: hidden size and learning rate chosen per test month on the month before it, then refit on all earlier months. GRU, dilated causal TCN and a two-layer transformer over the last L minutes of return, volume ratio and taker-buy share, plus lead and hour. Last column: accuracy minus the simple baseline on the same windows, day-block 95% interval; 'chosen h' lists the hidden size picked for each test month.\n\n")
        f.write("| minute | model | L | n | accuracy [95% CI] | AUC | log loss | vs baseline | chosen h |\n|---|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote sequence2.md")


if __name__ == "__main__":
    main()
