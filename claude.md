# Crypto Swing Trading Bot — Project Spec

## Overview

Build a Python-based crypto swing trading bot that runs once daily, evaluates trend-following signals on Binance spot markets, executes trades automatically, and includes a backtester to validate strategy performance before deploying real capital.

---

## Project Structure

```
crypto-swing-bot/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── config.py
├── data/
│   └── fetcher.py
├── signals/
│   └── indicators.py
├── strategy/
│   └── swing.py
├── backtest/
│   └── engine.py
├── execution/
│   └── binance_client.py
├── logs/
│   └── trades.log
├── main.py
└── backtest_run.py
```

---

## Dependencies (`requirements.txt`)

```
python-binance
pandas
pandas-ta
numpy
matplotlib
python-dotenv
schedule
requests
```

---

## Configuration (`config.py`)

- Load API keys from a `.env` file (`BINANCE_API_KEY`, `BINANCE_API_SECRET`)
- Define a `WATCHLIST` — list of trading pairs to monitor, e.g. `["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]`
- Define `TRADE_AMOUNT_USDT` — fixed dollar amount per trade (e.g. `100`)
- Define `STOP_LOSS_PCT` — e.g. `0.04` (4%)
- Define `TAKE_PROFIT_RSI` — RSI level to trigger take-profit, e.g. `65`
- Define `BUY_RSI_MAX` — max RSI to allow a buy entry, e.g. `42`
- Define `EMA_FAST` = `50`, `EMA_SLOW` = `200`
- Define `BACKTEST_START` — ISO date string, e.g. `"2022-01-01"`
- Define `DRY_RUN` — boolean. When `True`, log trade decisions but do not execute real orders.

---

## Data Fetcher (`data/fetcher.py`)

Implement `fetch_ohlcv(symbol: str, interval: str = "1d", limit: int = 300) -> pd.DataFrame`

- Use `python-binance` `Client.get_klines()` to fetch daily OHLCV candles
- Return a DataFrame with columns: `open_time`, `open`, `high`, `low`, `close`, `volume` — all numeric
- `open_time` should be a proper `datetime` index

Implement `fetch_historical(symbol: str, start: str, end: str = None) -> pd.DataFrame`

- Same structure but fetches from `start` date to `end` (or today)
- Handle Binance's 1000-candle limit by paginating requests in a loop

---

## Indicators (`signals/indicators.py`)

Implement `add_indicators(df: pd.DataFrame) -> pd.DataFrame`

Using `pandas-ta`:
- Add EMA columns: `ema_fast` (50-day), `ema_slow` (200-day)
- Add RSI column: `rsi` (14-period)
- Add ATR column: `atr` (14-period) — used for optional dynamic stop-loss sizing

Return the DataFrame with these columns appended. Drop rows where indicators are NaN (first ~200 rows).

---

## Strategy (`strategy/swing.py`)

Implement `generate_signals(df: pd.DataFrame) -> pd.DataFrame`

Add a `signal` column to the DataFrame with values:
- `"BUY"` — when all of the following are true on the latest closed candle:
  - `ema_fast > ema_slow` (uptrend confirmed)
  - `rsi < BUY_RSI_MAX` (short-term pullback — not chasing)
  - No open position already held for this symbol
- `"SELL"` — when any of the following are true:
  - `rsi > TAKE_PROFIT_RSI` (overbought)
  - `close < entry_price * (1 - STOP_LOSS_PCT)` (stop loss hit)
  - `ema_fast < ema_slow` (trend reversal)
- `"HOLD"` — otherwise

The strategy module should be stateless — it only evaluates the latest row. Position state is managed by the execution layer.

---

## Backtester (`backtest/engine.py`)

Implement `run_backtest(symbol: str, start: str, end: str = None) -> dict`

Logic:
1. Fetch full historical OHLCV via `fetch_historical()`
2. Add indicators
3. Walk forward through each candle (no lookahead — decisions made using data up to and including row `i`)
4. Track open position: entry price, entry date
5. On each candle apply the same BUY/SELL logic from the strategy
6. Simulate execution at next candle's open price (to avoid lookahead on same-candle fill)
7. Deduct 0.1% per trade (Binance taker fee) on both entry and exit
8. Track a running portfolio value starting at `$1000`

Return a `dict` containing:
- `total_return_pct`
- `num_trades`
- `win_rate`
- `max_drawdown_pct`
- `sharpe_ratio` (annualized, risk-free rate = 0)
- `trade_log` — list of dicts, each with `symbol`, `entry_date`, `exit_date`, `entry_price`, `exit_price`, `pnl_pct`, `result` (`"win"` or `"loss"`)

Implement `plot_results(symbol: str, df: pd.DataFrame, trade_log: list)`

- Plot close price with EMA lines overlaid
- Mark BUY entries (green triangle up) and SELL exits (red triangle down) on the price chart
- Plot portfolio value over time in a subplot below
- Save to `logs/{symbol}_backtest.png`

---

## Binance Execution Client (`execution/binance_client.py`)

Implement a `BinanceTrader` class:

**`__init__`**: Initialize `python-binance` Client with API key/secret from config. Load position state from `logs/positions.json` (dict mapping symbol → entry price, or empty if no open position).

**`get_balance(asset: str = "USDT") -> float`**: Return free USDT balance.

**`buy(symbol: str, usdt_amount: float)`**:
- Place a market buy order for `usdt_amount` of `symbol`
- Record entry price and timestamp in `logs/positions.json`
- Log the trade to `logs/trades.log`
- If `DRY_RUN=True`, skip the API call but log as if it happened

**`sell(symbol: str)`**:
- Place a market sell order for the full held quantity of `symbol`
- Remove position from `logs/positions.json`
- Log the trade to `logs/trades.log`
- If `DRY_RUN=True`, skip the API call but log as if it happened

**`get_open_positions() -> dict`**: Return the current positions dict from `logs/positions.json`.

---

## Main Loop (`main.py`)

Implement `run_bot()`:

1. For each symbol in `WATCHLIST`:
   a. Fetch latest 300 daily candles
   b. Add indicators
   c. Generate signal for the latest candle
   d. If signal is `"BUY"` and no open position for this symbol: call `trader.buy()`
   e. If signal is `"SELL"` and an open position exists: call `trader.sell()`
   f. Log the decision (BUY, SELL, or HOLD) with the RSI and EMA values at time of decision

2. Use `schedule` to run `run_bot()` once per day at `08:00 UTC` (shortly after daily candle close)

Print a summary table to stdout after each run: symbol, signal, RSI, EMA fast, EMA slow, position status.

---

## Backtest Runner (`backtest_run.py`)

Simple script that:
1. Runs `run_backtest()` for each symbol in `WATCHLIST`
2. Prints a formatted summary table for each: total return, win rate, number of trades, max drawdown, Sharpe
3. Saves the plot for each symbol
4. Prints a combined portfolio return assuming equal allocation across all symbols

---

## Logging

All trade events should be appended to `logs/trades.log` in this format:
```
2024-11-15 08:01:32 | BUY  | BTCUSDT | price=91240.50 | usdt=100.00 | rsi=38.2 | dry_run=True
2024-11-18 08:00:55 | SELL | BTCUSDT | price=96100.00 | entry=91240.50 | pnl=+5.33% | reason=RSI_TP
```

The `reason` field on SELL should be one of: `RSI_TP`, `STOP_LOSS`, `TREND_REVERSAL`.

---

## `.env` file (user must create this)

```
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
```

The bot must never hardcode credentials. Raise a clear error at startup if keys are missing.

---

## Important Implementation Notes

- **Always start with `DRY_RUN=True`**. The README should make this very clear. The user should run the backtester and paper trade for at least 2-4 weeks before switching to live.
- Use Binance **spot** trading only. No margin, no futures.
- The bot should never risk more than `TRADE_AMOUNT_USDT` per position. Never use dynamic sizing in the first version.
- Handle Binance API errors gracefully — catch exceptions, log the error, and continue to the next symbol rather than crashing.
- `pandas-ta` sometimes has issues with certain pandas versions — pin `pandas==2.0.3` and `pandas-ta==0.3.14b` in requirements if needed.
- Binance is not available to US users without using Binance.US (`tld='us'` in the Client constructor). Add a `BINANCE_TLD` config option defaulting to `'com'`.