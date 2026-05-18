from backtest.engine import run_backtest, plot_results
import config


def main():
    results = []
    for symbol in config.WATCHLIST:
        print(f"\nRunning backtest for {symbol}...")
        try:
            r = run_backtest(symbol, start=config.BACKTEST_START)
            df = r.pop("_df")
            pv = r.pop("_portfolio_values")
            buys = r.pop("_buy_signals")
            sells = r.pop("_sell_signals")

            path = plot_results(symbol, df, r["trade_log"], pv, buys, sells)
            print(f"  Chart saved: {path}")
            _print_result(r)
            results.append(r)
        except Exception as e:
            print(f"  ERROR: {e}")

    if results:
        _print_combined(results)


def _print_result(r: dict):
    print(f"  Total return : {r['total_return_pct']:+.2f}%")
    print(f"  Trades       : {r['num_trades']}")
    print(f"  Win rate     : {r['win_rate']:.1f}%")
    print(f"  Max drawdown : {r['max_drawdown_pct']:.2f}%")
    print(f"  Sharpe ratio : {r['sharpe_ratio']:.3f}")


def _print_combined(results: list):
    n = len(results)
    print("\n" + "=" * 50)
    print(f"COMBINED PORTFOLIO ({n} symbols, equal weight)")
    print("=" * 50)
    combined_return = sum(r["total_return_pct"] for r in results) / n
    print(f"  Avg return   : {combined_return:+.2f}%")
    print()


if __name__ == "__main__":
    main()
