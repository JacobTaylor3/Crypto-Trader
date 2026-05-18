import os
from dotenv import load_dotenv

load_dotenv()

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
BINANCE_TLD = os.getenv("BINANCE_TLD", "com")

WATCHLIST = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]

TRADE_AMOUNT_USDT = 20.0       # fallback minimum if balance is too low
TRADE_BALANCE_PCT = 0.25      # use 25% of free USDT balance per trade (holds up to 4 positions)
STOP_LOSS_PCT = 0.04
TAKE_PROFIT_RSI = 65
BUY_RSI_MAX = 42

EMA_FAST = 50
EMA_SLOW = 200

BACKTEST_START = "2022-01-01"

# Per-symbol overrides — tuned via tune.py grid search (2022–2026)
SYMBOL_PARAMS = {
    "BTCUSDT": {"BUY_RSI_MAX": 40, "TAKE_PROFIT_RSI": 65, "STOP_LOSS_PCT": 0.04},
    "ETHUSDT": {"BUY_RSI_MAX": 35, "TAKE_PROFIT_RSI": 60, "STOP_LOSS_PCT": 0.04},
    "SOLUSDT": {"BUY_RSI_MAX": 35, "TAKE_PROFIT_RSI": 65, "STOP_LOSS_PCT": 0.08},
    "BNBUSDT": {"BUY_RSI_MAX": 35, "TAKE_PROFIT_RSI": 60, "STOP_LOSS_PCT": 0.08},
}


def get_params(symbol: str) -> dict:
    defaults = {
        "BUY_RSI_MAX": BUY_RSI_MAX,
        "TAKE_PROFIT_RSI": TAKE_PROFIT_RSI,
        "STOP_LOSS_PCT": STOP_LOSS_PCT,
    }
    return {**defaults, **SYMBOL_PARAMS.get(symbol, {})}

DRY_RUN = False


def require_api_keys():
    if not BINANCE_API_KEY or not BINANCE_API_SECRET:
        raise EnvironmentError(
            "BINANCE_API_KEY and BINANCE_API_SECRET must be set in your .env file. "
            "See .env.example for the expected format."
        )
