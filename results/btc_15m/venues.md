The boundary reversal on other venues, 2025-10 to 2026-08, minute 0, walk-forward by month. Each venue's windows are labelled by its own candles; Coinbase and Bitstamp are restricted to windows Binance also has. Coinbase and Bitstamp candles carry no taker-side volume, so the forest uses price features only. Last column: minus prev-window on the same windows, day-block 95% interval.

| venue | model | windows | share up | accuracy [95% CI] | minus prev-window |
|---|---|---|---|---|---|
| Binance BTC-USDT | prev-window | 23328 | 49.7% | 52.21% [51.63, 52.82] |  |
| Binance BTC-USDT | forest, price features | 23328 | 49.7% | 52.49% [51.94, 53.07] | +0.28 [-0.32, +0.91] |
| Coinbase BTC-USD | prev-window | 22648 | 49.7% | 51.95% [51.36, 52.54] |  |
| Coinbase BTC-USD | forest, price features | 22648 | 49.7% | 52.27% [51.70, 52.84] | +0.32 [-0.31, +0.98] |
| Bitstamp BTC-USD | prev-window | 23328 | 50.1% | 52.06% [51.47, 52.68] |  |
| Bitstamp BTC-USD | forest, price features | 23328 | 50.1% | 52.06% [51.50, 52.69] | -0.00 [-0.66, +0.70] |

Transfer in time order: a forest trained on Bitcoin's earlier months (Binance, price + flow features) scores ETH and SOL each test month, against each coin's own-history forest and its prev-window baseline. Last column: minus prev-window on the same windows.

| coin | model | windows | accuracy [95% CI] | minus prev-window |
|---|---|---|---|---|
| ETH | prev-window (own) | 23328 | 52.76% [52.16, 53.33] |  |
| ETH | forest, own history | 23328 | 53.06% [52.49, 53.64] | +0.30 [-0.34, +0.93] |
| ETH | forest trained on BTC | 23328 | 53.31% [52.62, 54.00] | +0.54 [-0.18, +1.27] |
| SOL | prev-window (own) | 23328 | 51.99% [51.38, 52.64] |  |
| SOL | forest, own history | 23328 | 52.26% [51.65, 52.89] | +0.27 [-0.40, +0.93] |
| SOL | forest trained on BTC | 23328 | 51.92% [51.32, 52.50] | -0.07 [-0.83, +0.66] |
