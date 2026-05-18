# Future Plans

## 4-Hour Candle Strategy
Switch from daily candles to 4-hour candles for more frequent signals.

**Benefits:**
- 6x more trading opportunities per day
- Catches entries and exits earlier
- Better reaction to intraday momentum shifts

**What needs to change:**
- `data/fetcher.py` — fetch 4h candles instead of 1d
- `backtest/engine.py` — update interval, adjust Sharpe annualization factor (√(365×6))
- `tune.py` — re-run grid search on 4h data to find optimal RSI/EMA/stop-loss params
- `main.py` — run every 4 hours instead of once daily
- Full re-backtest and re-tune before going live

**When to do this:** After the daily strategy has run live for 2-4 weeks and proven stable.
