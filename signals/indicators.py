import pandas as pd
import pandas_ta as ta
import config


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Assign directly instead of append=True — avoids pandas 2.x / pandas-ta compat issue
    df["ema_fast"] = df.ta.ema(length=config.EMA_FAST)
    df["ema_slow"] = df.ta.ema(length=config.EMA_SLOW)
    df["rsi"] = df.ta.rsi(length=14)
    df["atr"] = df.ta.atr(length=14)
    df.dropna(subset=["ema_fast", "ema_slow", "rsi"], inplace=True)
    return df
