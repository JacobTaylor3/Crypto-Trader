# Crypto Trading Bot

A Python-based automated trading bot for Binance spot markets. Supports multiple strategies — currently running the EMA/RSI swing strategy, with Dual Momentum planned next.

> **WARNING: `DRY_RUN = True` is the default. The bot will NOT place real orders until you explicitly set `DRY_RUN = False` in `config.py`. Run the backtester and paper-trade for at least 2–4 weeks before touching real capital.**

---

## Strategies

### Swing (EMA + RSI) — Current
- **Trend filter**: EMA 50 must be above EMA 200 (uptrend confirmed)
- **Entry**: RSI < 35–40 depending on coin (short-term pullback)
- **Take-profit**: RSI > 60–65 depending on coin (overbought)
- **Stop-loss**: 4–8% below entry price depending on coin
- **Exit on trend reversal**: EMA 50 crosses below EMA 200
- Runs once daily at **00:15 UTC** after candle close
- Backtested 2022–2026: ~+74% combined average across 4 coins

### Dual Momentum — Planned
- Every month, rotate 100% of capital into the strongest performing coin
- Highest upside potential in bull markets
- See `future-plans.md` for details

---

## Setup

### 1. Install dependencies

```bash
pip install setuptools --break-system-packages
pip install -r requirements.txt --break-system-packages
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Edit `.env` and paste your Binance API keys. US users: set `BINANCE_TLD=us`.

**The bot will not start if keys are missing (unless `DRY_RUN=True`).**

### 3. Configure the bot

Edit `config.py` to adjust:
- `WATCHLIST` — pairs to monitor
- `TRADE_BALANCE_PCT` — fraction of free USDT to use per trade (default 25%)
- `TRADE_AMOUNT_USDT` — minimum trade size fallback
- `DRY_RUN` — keep `True` until you've validated the strategy
- `BINANCE_TLD` — `'com'` (default) or `'us'`

---

## Running the Swing Strategy

**Live bot:**
```bash
nohup python3 run_swing.py > logs/bot.log 2>&1 &
```

**Backtest:**
```bash
python3 backtest_swing.py
```

**Parameter tuning:**
```bash
python3 tune.py
```

**Stop the bot:**
```bash
pkill -f run_swing.py
```

**Check activity:**
```bash
tail -f logs/trades.log
```

---

## Logs

| File | Contents |
|---|---|
| `logs/trades.log` | Every BUY/SELL event with price, RSI, and P&L |
| `logs/positions.json` | Currently open positions (persisted between runs) |
| `logs/{SYMBOL}_backtest.png` | Backtest chart with trade markers |
| `logs/bot.log` | Bot runtime output and errors |

---

## Project Structure

```
├── config.py                  # All configurable parameters
├── run_swing.py               # Swing strategy live bot
├── backtest_swing.py          # Swing strategy backtester
├── tune.py                    # Parameter grid search
├── future-plans.md            # Roadmap for new strategies
├── data/fetcher.py            # Binance OHLCV data fetching
├── signals/indicators.py      # EMA / RSI / ATR calculation
├── strategy/swing.py          # Swing signal generation logic
├── execution/binance_client.py# Live order execution
├── backtest/engine.py         # Walk-forward backtester + plotting
├── logs/                      # Trade logs and charts
└── requirements.txt
```

---

## Disclaimer

This software is for educational purposes only. Cryptocurrency trading carries significant risk of loss. Always test thoroughly in dry-run mode before risking real capital.
