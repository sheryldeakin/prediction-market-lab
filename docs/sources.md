# Sources

Every external source used in this repo, with what it was used for. Primary means the data or document itself; secondary means someone's description of it.

| date | source | URL | type | used for |
|---|---|---|---|---|
| 2026-09-30 | Binance public market data, spot 1-minute klines for BTCUSDT | https://data.binance.vision/?prefix=data/spot/monthly/klines/BTCUSDT/1m/ | primary | Training and evaluation data for `models/btc_15m` (prices, volume, trade count, taker-buy volume) |
| 2026-09-30 | Binance kline column layout (open_time, open, high, low, close, volume, close_time, quote_volume, count, taker_buy_base, taker_buy_quote, ignore) | https://github.com/binance/binance-public-data | primary | Column names in `models/btc_15m/data.py`; timestamp units changed from milliseconds to microseconds in 2025 |
| 2026-09-30 | XGBoost Python package documentation | https://xgboost.readthedocs.io/ | primary | Model parameters in `models/btc_15m/evaluate.py` |
| 2026-09-30 | The Quarter-Hour Effect: Periodic Algorithmic Trading and Return Predictability in Cryptocurrency Futures (arXiv 2607.09426) | https://arxiv.org/abs/2607.09426 | primary (abstract read; full results not checked) | Motivation for tick-level order flow at quarter-hour openings in "What to test next" |
| 2026-09-30 | When Alpha Disappears: A One-Switch Benchmark for Decision-Time Leakage in Financial Backtests (arXiv 2605.23959) | https://arxiv.org/abs/2605.23959 | primary (abstract read) | The caution about published high accuracies and decision-time leakage |
| 2026-09-30 | Purged cross-validation (Wikipedia summary of Lopez de Prado, Advances in Financial Machine Learning, 2018) | https://en.wikipedia.org/wiki/Purged_cross-validation | secondary | Combinatorial purged cross-validation with an embargo, listed in "What to test next" |
| 2026-09-30 | Short-term bitcoin market prediction via machine learning (Journal of Finance and Data Science, 2021) | https://www.sciencedirect.com/science/article/pii/S2405918821000027 | secondary (search-result summary only; the page returned 403) | The claim that recurrent networks and gradient boosting are the model families to compare at short horizons |
| 2026-09-30 | Binance public market data, spot aggregated trades for BTCUSDT | https://data.binance.vision/?prefix=data/spot/monthly/aggTrades/BTCUSDT/ | primary | Tick-level order-flow features in `models/btc_15m/ticks.py`; `is_buyer_maker` gives the aggressor side |
| 2026-09-30 | PyTorch (CUDA build) | https://pytorch.org/ | primary | GRU sequence model in `models/btc_15m/sequence.py` |
| 2026-09-30 | scikit-learn: RandomForestClassifier, HistGradientBoostingClassifier | https://scikit-learn.org/stable/ | primary | Forest and histogram gradient boosting models |
