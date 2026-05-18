import pandas as pd
import config


def generate_signals(df: pd.DataFrame, position: dict = None, params: dict = None) -> pd.DataFrame:
    """Evaluate each candle and append a 'signal' column.

    position: {"entry_price": float} if a position is held, else None.
    params: per-symbol overrides from config.get_params(). Falls back to config globals.
    """
    p = params or {
        "BUY_RSI_MAX": config.BUY_RSI_MAX,
        "TAKE_PROFIT_RSI": config.TAKE_PROFIT_RSI,
        "STOP_LOSS_PCT": config.STOP_LOSS_PCT,
    }
    df = df.copy()
    signals = ["HOLD"] * len(df)

    for i in range(len(df)):
        row = df.iloc[i]
        uptrend = row["ema_fast"] > row["ema_slow"]

        if position is None:
            if uptrend and row["rsi"] < p["BUY_RSI_MAX"]:
                signals[i] = "BUY"
        else:
            entry = position["entry_price"]
            if row["rsi"] > p["TAKE_PROFIT_RSI"]:
                signals[i] = "SELL"
            elif row["close"] < entry * (1 - p["STOP_LOSS_PCT"]):
                signals[i] = "SELL"
            elif not uptrend:
                signals[i] = "SELL"

    df["signal"] = signals
    return df


def sell_reason(row: pd.Series, entry_price: float, params: dict = None) -> str:
    """Return the highest-priority sell reason for a row."""
    p = params or {
        "TAKE_PROFIT_RSI": config.TAKE_PROFIT_RSI,
        "STOP_LOSS_PCT": config.STOP_LOSS_PCT,
    }
    if row["rsi"] > p["TAKE_PROFIT_RSI"]:
        return "RSI_TP"
    if row["close"] < entry_price * (1 - p["STOP_LOSS_PCT"]):
        return "STOP_LOSS"
    return "TREND_REVERSAL"
