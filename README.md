# Crypto Swing Trading Bot

A Python-based daily swing trading bot for Binance spot markets using EMA 50/200 trend-following and RSI-based entry/exit signals.

> **WARNING: `DRY_RUN = True` is the default. The bot will NOT place real orders until you explicitly set `DRY_RUN = False` in `config.py`. Run the backtester and paper-trade for at least 2–4 weeks before touching real capital.**

---

## Strategy

- **Trend filter**: EMA 50 must be above EMA 200 (uptrend confirmed)
- **Entry**: RSI < 42 (short-term pullback — not chasing)
- **Take-profit**: RSI > 65 (overbought)
- **Stop-loss**: Close drops 4% below entry price
- **Exit on trend reversal**: EMA 50 crosses below EMA 200

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> **Known issue**: `pandas-ta==0.3.14b` may not install cleanly on Python 3.12+. If you hit errors, try Python 3.10 or 3.11, or install from the GitHub source directly.

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Edit `.env` and paste your Binance API keys. US users: set `BINANCE_TLD=us`.

**The bot will not start if keys are missing (unless `DRY_RUN=True`).**

### 3. Configure the bot

Edit `config.py` to adjust:
- `WATCHLIST` — pairs to monitor
- `TRADE_AMOUNT_USDT` — fixed dollar size per trade
- `DRY_RUN` — keep `True` until you've validated the strategy
- `BINANCE_TLD` — `'com'` (default) or `'us'`

---

## Running the bot

```bash
python main.py
```

Runs immediately, then schedules itself to run daily at **08:00 UTC** (shortly after the daily candle closes).

---

## Running the backtester

```bash
python backtest_run.py
```

Runs a full historical backtest for every symbol in `WATCHLIST` from `BACKTEST_START`. Prints a summary table and saves a chart to `logs/{SYMBOL}_backtest.png`.

---

## Logs

| File | Contents |
|---|---|
| `logs/trades.log` | Every BUY/SELL event with price, RSI, and P&L |
| `logs/positions.json` | Currently open positions (persisted between runs) |
| `logs/{SYMBOL}_backtest.png` | Backtest chart with trade markers |

---

## Project Structure

```
├── config.py              # All configurable parameters
├── main.py                # Bot entry point and scheduler
├── backtest_run.py        # Backtest runner script
├── data/fetcher.py        # Binance OHLCV data fetching
├── signals/indicators.py  # EMA / RSI / ATR calculation
├── strategy/swing.py      # Signal generation logic
├── execution/             # Live order execution
│   └── binance_client.py
├── backtest/engine.py     # Walk-forward backtester + plotting
├── logs/                  # Trade logs and charts
└── requirements.txt
```

---

## Disclaimer

This software is for educational purposes only. Cryptocurrency trading carries significant risk of loss. Always test thoroughly in dry-run mode before risking real capital.
