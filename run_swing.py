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

_SCHEDULE_TIME = "00:15"


def _next_run_str() -> str:
    job = next(iter(schedule.jobs), None)
    if job and job.next_run:
        return job.next_run.strftime("%Y-%m-%d %H:%M UTC")
    return f"tomorrow at {_SCHEDULE_TIME} UTC"


def run_bot():
    _log.info("=== Bot run starting (DRY_RUN=%s) ===", config.DRY_RUN)
    trader = BinanceTrader()
    positions = trader.get_open_positions()

    open_count = len(positions)
    _log.info("Open positions: %d — %s", open_count, list(positions.keys()) or "none")

    # Snapshot balance once so all BUYs this run use the same 25% slice.
    balance = trader.get_balance()
    trade_amount = max(balance * config.TRADE_BALANCE_PCT, config.TRADE_AMOUNT_USDT)
    _log.info("Balance: $%.2f USDT — trade amount per position: $%.2f (%.0f%%)",
              balance, trade_amount, config.TRADE_BALANCE_PCT * 100)

    rows = []
    trades_executed = 0
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
                trader.buy(symbol, trade_amount, rsi=rsi, current_price=float(last["close"]))
                trades_executed += 1
            elif signal == "SELL" and position is not None:
                reason = sell_reason(last, position["entry_price"], params=params)
                trader.sell(symbol, current_price=float(last["close"]), reason=reason)
                trades_executed += 1

            rows.append((symbol, signal, f"{rsi:.1f}", f"{ema_f:.2f}", f"{ema_s:.2f}", pos_status))

        except Exception as e:
            _log.error("Error processing %s: %s", symbol, e)
            rows.append((symbol, "ERROR", "-", "-", "-", "-"))

    _print_summary(rows)

    if trades_executed == 0:
        _log.info("No trades executed this run — all signals were HOLD or conditions not met.")
    else:
        _log.info("%d trade(s) executed this run.", trades_executed)

    _log.info("=== Bot run complete. Next run: %s ===", _next_run_str())


def _print_summary(rows):
    header = f"{'Symbol':<10} {'Signal':<6} {'RSI':>6} {'EMA_F':>10} {'EMA_S':>10} {'Position':<20}"
    print("\n" + header)
    print("-" * len(header))
    for symbol, signal, rsi, ema_f, ema_s, pos in rows:
        print(f"{symbol:<10} {signal:<6} {rsi:>6} {ema_f:>10} {ema_s:>10} {pos:<20}")
    print()


if __name__ == "__main__":
    _log.info("=== Swing bot starting up (DRY_RUN=%s, watchlist=%s) ===",
              config.DRY_RUN, config.WATCHLIST)
    schedule.every().day.at(_SCHEDULE_TIME, "UTC").do(run_bot)
    _log.info("Scheduler ready — running immediately, then daily at %s UTC.", _SCHEDULE_TIME)
    run_bot()
    while True:
        schedule.run_pending()
        time.sleep(60)
