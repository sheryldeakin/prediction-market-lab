"""A small sequence model on the raw minute series, evaluated the same way as the
feature models: walk-forward by month, against the majority and lead-only baselines.

Input for a window at entry minute k: the last L one-minute steps up to minute k, each
step = (log return in bp, log volume ratio to the 24-hour mean, taker-buy share minus
0.5). Model: GRU (hidden 32) over the sequence, plus the lead and the hour as extra
inputs to the head. Trained with early stopping on the last 10% of the training
months. Deterministic seeds; runs on CUDA when available, else CPU.

    python -m models.btc_15m.sequence --start 2025-10 --end 2026-08 --minutes 0,3
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import log_loss, roc_auc_score

from models.btc_15m.data import load
from models.btc_15m.features import HISTORY, Series, dataset
from models.btc_15m.stats import block_bootstrap_ci, paired_difference_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
L = 120
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class GRUNet(nn.Module):
    def __init__(self, n_in=3, hidden=32, n_extra=2):
        super().__init__()
        self.gru = nn.GRU(n_in, hidden, batch_first=True)
        self.head = nn.Sequential(nn.Linear(hidden + n_extra, 32), nn.ReLU(), nn.Dropout(0.2), nn.Linear(32, 1))

    def forward(self, seq, extra):
        _, h = self.gru(seq)
        return self.head(torch.cat([h[-1], extra], dim=1)).squeeze(1)


def build_sequences(s: Series, k: int):
    """Sequences ending at the last closed candle before minute k; returns X, extra, y, t."""
    vol24 = pd.Series(s.v).rolling(1440).mean().values
    share = np.where(s.v > 0, (s.csv[1:] - s.csv[:-1]) / (2 * np.maximum(s.v, 1e-9)) + 0.5, 0.5) - 0.5
    lv = np.log((s.v + 1e-9) / (vol24 + 1e-9))
    steps = np.stack([s.r1 / 10.0, np.nan_to_num(lv), share * 2], axis=1).astype(np.float32)
    X, extra, y, t = [], [], [], []
    for i in s.window_starts():
        j = i + k
        if i < HISTORY or not s.ok[i - HISTORY:i + 15].all():
            continue
        X.append(steps[j - L:j])
        lead = (s.c[j - 1] / s.o[i] - 1) * 1e4 if k else 0.0
        extra.append([lead / 10.0, (s.t[i] // 3600 % 24) / 24.0])
        y.append(s.label(i))
        t.append(int(s.t[i]))
    return np.stack(X), np.array(extra, dtype=np.float32), np.array(y), np.array(t)


def fit(X, E, y, seed=0, epochs=15):
    torch.manual_seed(seed)
    np.random.seed(seed)
    n = len(y)
    cut = int(n * 0.9)
    model = GRUNet().to(DEV)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    lossf = nn.BCEWithLogitsLoss()
    Xt, Et, yt = torch.tensor(X).to(DEV), torch.tensor(E).to(DEV), torch.tensor(y, dtype=torch.float32).to(DEV)
    best, best_state, bad = 1e9, None, 0
    for ep in range(epochs):
        model.train()
        perm = torch.randperm(cut, device=DEV)
        for b in range(0, cut, 512):
            idx = perm[b:b + 512]
            opt.zero_grad()
            lossf(model(Xt[idx], Et[idx]), yt[idx]).backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            vl = lossf(model(Xt[cut:], Et[cut:]), yt[cut:]).item()
        if vl < best - 1e-4:
            best, best_state, bad = vl, {k: v.clone() for k, v in model.state_dict().items()}, 0
        else:
            bad += 1
            if bad >= 3:
                break
    model.load_state_dict(best_state)
    return model


def predict(model, X, E):
    model.eval()
    with torch.no_grad():
        return torch.sigmoid(model(torch.tensor(X).to(DEV), torch.tensor(E).to(DEV))).cpu().numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--minutes", default="0,3")
    a = ap.parse_args()
    s = Series(load(a.start, a.end))
    rows = []
    for k in [int(x) for x in a.minutes.split(",")]:
        X, E, y, t = build_sequences(s, k)
        month = pd.to_datetime(t, unit="s").to_period("M")
        pred = np.full(len(y), np.nan)
        for m in sorted(set(month))[3:]:
            tr, te = month < m, month == m
            model = fit(X[tr], E[tr], y[tr])
            pred[te] = predict(model, X[te], E[te])
            print(f"k={k} test {m}: acc {((pred[te] > .5) == y[te]).mean()*100:.2f}%", flush=True)
        keep = ~np.isnan(pred)
        p, yy, tt = pred[keep], y[keep], t[keep]
        hits = ((p > 0.5) == yy).astype(float)
        m_, lo, hi = block_bootstrap_ci(hits, tt)
        # baseline on the same windows from the feature table (lead-only at k>0, majority at k=0)
        D = dataset(s, k)
        base = D.set_index("t").reindex(tt)
        if k > 0:
            from sklearn.linear_model import LogisticRegression
            bm = pd.to_datetime(D.t, unit="s").dt.to_period("M")
            bp = np.full(len(D), np.nan)
            for mm in sorted(bm.unique())[3:]:
                trm, tem = (bm < mm).values, (bm == mm).values
                bp[tem] = LogisticRegression(max_iter=500).fit(D.loc[trm, ["lead"]], D.y[trm]).predict_proba(D.loc[tem, ["lead"]])[:, 1]
            bpred = pd.Series(bp, index=D.t.values).reindex(tt).values
            bname = "lead-only"
        else:
            bpred = np.full(len(tt), D.y.mean())
            bname = "majority"
        bhits = ((bpred > 0.5) == yy).astype(float)
        d, dlo, dhi = paired_difference_ci(hits, bhits, tt)
        rows.append([k, "gru-sequence", len(yy), f"{m_*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", f"{roc_auc_score(yy, p):.3f}",
                     f"{log_loss(yy, np.clip(p, 1e-6, 1-1e-6)):.4f}", f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}] vs {bname}"])
        print(rows[-1], flush=True)
    with open(OUT / "sequence.md", "w") as f:
        f.write(f"GRU over the last {L} minutes (return, volume ratio, taker-buy share) plus lead and hour, walk-forward by month, early stopping on the last 10% of training months.\n\n")
        f.write("| minute | model | n | accuracy [95% CI] | AUC | log loss | vs baseline |\n|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")


if __name__ == "__main__":
    main()
