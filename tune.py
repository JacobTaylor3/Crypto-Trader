"""
Grid search over key strategy parameters. Monkey-patches config at runtime
so the core engine code doesn't need to change.
"""
import itertools
import config
from backtest.engine import run_backtest

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
START = config.BACKTEST_START

GRID = {
    "BUY_RSI_MAX":      [35, 40, 45],
    "TAKE_PROFIT_RSI":  [60, 65, 70],
    "STOP_LOSS_PCT":    [0.04, 0.06, 0.08],
}

keys = list(GRID.keys())
combos = list(itertools.product(*[GRID[k] for k in keys]))
print(f"Testing {len(combos)} parameter combinations across {len(SYMBOLS)} symbols...\n")


def run_with_params(symbol, params):
    for k, v in params.items():
        setattr(config, k, v)
    r = run_backtest(symbol, start=START)
    # strip internal keys
    r.pop("_df", None)
    r.pop("_portfolio_values", None)
    r.pop("_buy_signals", None)
    r.pop("_sell_signals", None)
    r.pop("trade_log", None)
    return r


best_overall = {}

for symbol in SYMBOLS:
    print(f"{'='*55}")
    print(f"  {symbol}")
    print(f"{'='*55}")

    results = []
    for combo in combos:
        params = dict(zip(keys, combo))
        try:
            r = run_with_params(symbol, params)
            results.append({**params, **r})
        except Exception as e:
            pass

    # Reset config to defaults
    config.BUY_RSI_MAX = 42
    config.TAKE_PROFIT_RSI = 65
    config.STOP_LOSS_PCT = 0.04

    # Rank by Sharpe, break ties by total return
    results.sort(key=lambda x: (x["sharpe_ratio"], x["total_return_pct"]), reverse=True)

    print(f"  {'RSI_BUY':<8} {'RSI_TP':<8} {'SL%':<6} {'Return':>8} {'WinRate':>8} {'MaxDD':>8} {'Sharpe':>8} {'Trades':>7}")
    print(f"  {'-'*68}")
    for r in results[:10]:
        print(
            f"  {r['BUY_RSI_MAX']:<8} {r['TAKE_PROFIT_RSI']:<8} {r['STOP_LOSS_PCT']*100:<5.0f}% "
            f"  {r['total_return_pct']:>+7.1f}% {r['win_rate']:>7.1f}% "
            f"  {r['max_drawdown_pct']:>6.1f}%  {r['sharpe_ratio']:>7.3f}  {r['num_trades']:>6}"
        )

    best = results[0]
    best_overall[symbol] = best
    print(f"\n  Best: RSI_BUY={best['BUY_RSI_MAX']} RSI_TP={best['TAKE_PROFIT_RSI']} SL={best['STOP_LOSS_PCT']*100:.0f}%\n")


print(f"\n{'='*55}")
print("  SUMMARY — Best params per symbol")
print(f"{'='*55}")
print(f"  {'Symbol':<10} {'RSI_BUY':<8} {'RSI_TP':<8} {'SL%':<6} {'Return':>8} {'Sharpe':>8}")
print(f"  {'-'*55}")
for sym, r in best_overall.items():
    print(
        f"  {sym:<10} {r['BUY_RSI_MAX']:<8} {r['TAKE_PROFIT_RSI']:<8} {r['STOP_LOSS_PCT']*100:<5.0f}% "
        f"  {r['total_return_pct']:>+7.1f}%  {r['sharpe_ratio']:>7.3f}"
    )
print()
