# Future Plans

## Script Structure
Each strategy has its own run and backtest script:

| Script | Purpose |
|---|---|
| `run_swing.py` | Live bot — EMA/RSI swing strategy (current) |
| `backtest_swing.py` | Backtest — EMA/RSI swing strategy (current) |
| `run_dual_momentum.py` | Live bot — Dual Momentum strategy (planned) |
| `backtest_dual_momentum.py` | Backtest — Dual Momentum strategy (planned) |

Run only one live strategy at a time to avoid conflicting orders on the same coins.

---

## Dual Momentum Strategy (Next)
Every month, rank coins in the watchlist by 30-day return. Put 100% of capital into the strongest performer. Rotate next month.

**Why it has the highest potential:**
- Automatically chases the strongest trending coin
- In bull markets crypto assets can go 5-10x in a single run
- Very few trades (~12/year), low fees

**What needs to be built:**
- `strategy/dual_momentum.py` — monthly ranking + rotation logic
- `run_dual_momentum.py` — live bot runner
- `backtest_dual_momentum.py` — backtest runner
- Full backtest and tune before going live

**When to do this:** After the swing strategy has run live for 2-4 weeks.

---

## 4-Hour Candle Strategy (Later)
Switch from daily candles to 4-hour candles for more frequent signals.

**Benefits:**
- 6x more trading opportunities per day
- Catches entries and exits earlier

**What needs to change:**
- `data/fetcher.py` — fetch 4h candles instead of 1d
- `backtest/engine.py` — update interval, adjust Sharpe annualization (√(365×6))
- `tune.py` — re-run grid search on 4h data
- Run every 4 hours instead of once daily

**When to do this:** After dual momentum is validated.
