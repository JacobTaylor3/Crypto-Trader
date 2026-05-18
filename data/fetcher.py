from datetime import datetime, timezone
import pandas as pd
from binance.client import Client
import config


def _make_client():
    return Client(config.BINANCE_API_KEY, config.BINANCE_API_SECRET, tld=config.BINANCE_TLD)


def _parse_klines(raw: list) -> pd.DataFrame:
    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_base", "taker_quote", "ignore",
    ])
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df.set_index("open_time", inplace=True)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col])
    return df[["open", "high", "low", "close", "volume"]]


def fetch_ohlcv(symbol: str, interval: str = "1d", limit: int = 300) -> pd.DataFrame:
    client = _make_client()
    raw = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    return _parse_klines(raw)


def fetch_historical(symbol: str, start: str, end: str = None) -> pd.DataFrame:
    client = _make_client()
    start_ms = int(datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp() * 1000)
    end_ms = (
        int(datetime.fromisoformat(end).replace(tzinfo=timezone.utc).timestamp() * 1000)
        if end
        else int(datetime.now(timezone.utc).timestamp() * 1000)
    )

    # Binance interval in ms for 1d
    interval_ms = 24 * 60 * 60 * 1000
    all_frames = []
    cursor = start_ms

    while cursor < end_ms:
        raw = client.get_klines(
            symbol=symbol,
            interval=Client.KLINE_INTERVAL_1DAY,
            startTime=cursor,
            endTime=end_ms,
            limit=1000,
        )
        if not raw:
            break
        all_frames.append(_parse_klines(raw))
        last_open_ms = raw[-1][0]
        cursor = last_open_ms + interval_ms
        if len(raw) < 1000:
            break

    if not all_frames:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    df = pd.concat(all_frames)
    df = df[~df.index.duplicated(keep="first")]
    df.sort_index(inplace=True)
    return df
