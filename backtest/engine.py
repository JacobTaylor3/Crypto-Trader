import os
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from data.fetcher import fetch_historical
from signals.indicators import add_indicators
from strategy.swing import sell_reason
import config

_FEE = 0.001  # 0.1% taker fee per side
_STARTING_CAPITAL = 1000.0


def run_backtest(symbol: str, start: str, end: str = None) -> dict:
    df = fetch_historical(symbol, start, end)
    df = add_indicators(df)
    df = df.reset_index()  # open_time becomes a column

    p = config.get_params(symbol)
    portfolio = _STARTING_CAPITAL
    position = None  # {"entry_price", "entry_date", "entry_idx"}
    trade_log = []
    portfolio_values = [portfolio] * len(df)
    buy_signals = []
    sell_signals = []

    # Evaluate signal on row i, fill at row i+1 open — so stop one before last
    for i in range(len(df) - 1):
        row = df.iloc[i]
        fill_row = df.iloc[i + 1]

        uptrend = row["ema_fast"] > row["ema_slow"]

        if position is None:
            if uptrend and row["rsi"] < p["BUY_RSI_MAX"]:
                entry_price = fill_row["open"] * (1 + _FEE)
                position = {
                    "entry_price": entry_price,
                    "entry_date": fill_row["open_time"],
                    "entry_idx": i + 1,
                }
                buy_signals.append(i + 1)
        else:
            entry = position["entry_price"]
            is_rsi_tp = row["rsi"] > p["TAKE_PROFIT_RSI"]
            is_stop = row["close"] < entry * (1 - p["STOP_LOSS_PCT"])
            is_reversal = not uptrend

            if is_rsi_tp or is_stop or is_reversal:
                reason = sell_reason(row, entry, params=p)
                exit_price = fill_row["open"] * (1 - _FEE)
                pnl_pct = (exit_price - entry) / entry
                portfolio *= (1 + pnl_pct)

                trade_log.append({
                    "symbol": symbol,
                    "entry_date": str(position["entry_date"]),
                    "exit_date": str(fill_row["open_time"]),
                    "entry_price": entry,
                    "exit_price": exit_price,
                    "pnl_pct": round(pnl_pct * 100, 4),
                    "result": "win" if pnl_pct > 0 else "loss",
                    "reason": reason,
                })
                sell_signals.append(i + 1)
                position = None

        portfolio_values[i + 1] = portfolio

    # Forward-fill final open position in portfolio curve (mark-to-market)
    if position is not None:
        last_close = df.iloc[-1]["close"]
        unreal_pnl = (last_close - position["entry_price"]) / position["entry_price"]
        portfolio_values[-1] = portfolio * (1 + unreal_pnl)

    total_return_pct = (portfolio_values[-1] - _STARTING_CAPITAL) / _STARTING_CAPITAL * 100
    num_trades = len(trade_log)
    wins = sum(1 for t in trade_log if t["result"] == "win")
    win_rate = wins / num_trades if num_trades else 0.0

    daily_returns = np.diff(portfolio_values) / np.array(portfolio_values[:-1])
    # √365: crypto trades every day of the year
    sharpe = (
        float(np.mean(daily_returns) / np.std(daily_returns) * math.sqrt(365))
        if np.std(daily_returns) > 0
        else 0.0
    )

    peak = _STARTING_CAPITAL
    max_dd = 0.0
    for v in portfolio_values:
        if v > peak:
            peak = v
        dd = (peak - v) / peak * 100
        if dd > max_dd:
            max_dd = dd

    return {
        "symbol": symbol,
        "total_return_pct": round(total_return_pct, 2),
        "num_trades": num_trades,
        "win_rate": round(win_rate * 100, 1),
        "max_drawdown_pct": round(max_dd, 2),
        "sharpe_ratio": round(sharpe, 3),
        "trade_log": trade_log,
        "_df": df,
        "_portfolio_values": portfolio_values,
        "_buy_signals": buy_signals,
        "_sell_signals": sell_signals,
    }


def plot_results(symbol: str, df, trade_log: list, portfolio_values: list,
                 buy_signals: list, sell_signals: list):
    os.makedirs("logs", exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True,
                                    gridspec_kw={"height_ratios": [3, 1]})

    dates = df["open_time"].tolist()
    ax1.plot(dates, df["close"], label="Close", color="black", linewidth=1)
    ax1.plot(dates, df["ema_fast"], label=f"EMA{config.EMA_FAST}", color="blue", linewidth=1)
    ax1.plot(dates, df["ema_slow"], label=f"EMA{config.EMA_SLOW}", color="orange", linewidth=1)

    for idx in buy_signals:
        ax1.scatter(dates[idx], df.iloc[idx]["close"], marker="^", color="green", zorder=5, s=80)
    for idx in sell_signals:
        ax1.scatter(dates[idx], df.iloc[idx]["close"], marker="v", color="red", zorder=5, s=80)

    ax1.set_title(f"{symbol} Backtest")
    ax1.set_ylabel("Price (USDT)")
    ax1.legend(loc="upper left")

    ax2.plot(dates, portfolio_values, color="purple", linewidth=1)
    ax2.set_ylabel("Portfolio ($)")
    ax2.set_xlabel("Date")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()

    plt.tight_layout()
    out_path = f"logs/{symbol}_backtest.png"
    plt.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path
