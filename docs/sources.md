# Sources

Every external source used in this repo, with what it was used for. Primary means the data or document itself; secondary means someone's description of it.

| date | source | URL | type | used for |
|---|---|---|---|---|
| 2026-09-30 | Binance public market data, spot 1-minute klines for BTCUSDT | https://data.binance.vision/?prefix=data/spot/monthly/klines/BTCUSDT/1m/ | primary | Training and evaluation data for `models/btc_15m` (prices, volume, trade count, taker-buy volume) |
| 2026-09-30 | Binance kline column layout (open_time, open, high, low, close, volume, close_time, quote_volume, count, taker_buy_base, taker_buy_quote, ignore) | https://github.com/binance/binance-public-data | primary | Column names in `models/btc_15m/data.py`; timestamp units changed from milliseconds to microseconds in 2025 |
| 2026-09-30 | XGBoost Python package documentation | https://xgboost.readthedocs.io/ | primary | Model parameters in `models/btc_15m/evaluate.py` |
