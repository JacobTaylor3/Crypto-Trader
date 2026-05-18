import logging
import schedule
import time

from data.fetcher import fetch_ohlcv
from signals.indicators import add_indicators
from strategy.swing import generate_signals, sell_reason
from execution.binance_client import BinanceTrader
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_log = logging.getLogger("bot")


def _trade_amount(trader: "BinanceTrader") -> float:
    balance = trader.get_balance()
    amount = balance * config.TRADE_BALANCE_PCT
    return max(amount, config.TRADE_AMOUNT_USDT)


def run_bot():
    _log.info("=== Bot run starting (DRY_RUN=%s) ===", config.DRY_RUN)
    trader = BinanceTrader()
    positions = trader.get_open_positions()

    rows = []
    for symbol in config.WATCHLIST:
        try:
            df = fetch_ohlcv(symbol, limit=300)
            df = add_indicators(df)
            position = positions.get(symbol)
            params = config.get_params(symbol)
            df = generate_signals(
                df,
                position={"entry_price": position["entry_price"]} if position else None,
                params=params,
            )

            last = df.iloc[-1]
            signal = last["signal"]
            rsi = last["rsi"]
            ema_f = last["ema_fast"]
            ema_s = last["ema_slow"]
            pos_status = f"OPEN@{position['entry_price']:.2f}" if position else "NONE"

            if signal == "BUY" and position is None:
                amount = _trade_amount(trader)
                trader.buy(symbol, amount, rsi=rsi, current_price=float(last["close"]))
            elif signal == "SELL" and position is not None:
                reason = sell_reason(last, position["entry_price"], params=params)
                trader.sell(symbol, current_price=float(last["close"]), reason=reason)

            rows.append((symbol, signal, f"{rsi:.1f}", f"{ema_f:.2f}", f"{ema_s:.2f}", pos_status))

        except Exception as e:
            _log.error("Error processing %s: %s", symbol, e)
            rows.append((symbol, "ERROR", "-", "-", "-", "-"))

    _print_summary(rows)
    _log.info("=== Bot run complete ===")


def _print_summary(rows):
    header = f"{'Symbol':<10} {'Signal':<6} {'RSI':>6} {'EMA_F':>10} {'EMA_S':>10} {'Position':<20}"
    print("\n" + header)
    print("-" * len(header))
    for symbol, signal, rsi, ema_f, ema_s, pos in rows:
        print(f"{symbol:<10} {signal:<6} {rsi:>6} {ema_f:>10} {ema_s:>10} {pos:<20}")
    print()


if __name__ == "__main__":
    run_bot()
    schedule.every().day.at("08:00", "UTC").do(run_bot)
    _log.info("Scheduler started — next run at 08:00 UTC daily.")
    while True:
        schedule.run_pending()
        time.sleep(60)
