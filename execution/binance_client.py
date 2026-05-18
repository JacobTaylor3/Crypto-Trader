import json
import logging
import os
from datetime import datetime, timezone

from binance.client import Client
from binance.exceptions import BinanceAPIException

import config

_POSITIONS_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "positions.json")
_LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "trades.log")

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("trader")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _append_log(line: str):
    os.makedirs(os.path.dirname(_LOG_FILE), exist_ok=True)
    with open(_LOG_FILE, "a") as f:
        f.write(line + "\n")


class BinanceTrader:
    def __init__(self):
        if not config.DRY_RUN:
            config.require_api_keys()
            self._client = Client(
                config.BINANCE_API_KEY,
                config.BINANCE_API_SECRET,
                tld=config.BINANCE_TLD,
            )
        else:
            self._client = None
        self._positions = self._load_positions()

    def _load_positions(self) -> dict:
        if os.path.exists(_POSITIONS_FILE):
            with open(_POSITIONS_FILE) as f:
                return json.load(f)
        return {}

    def _save_positions(self):
        os.makedirs(os.path.dirname(_POSITIONS_FILE), exist_ok=True)
        with open(_POSITIONS_FILE, "w") as f:
            json.dump(self._positions, f, indent=2)

    def get_balance(self, asset: str = "USDT") -> float:
        if config.DRY_RUN:
            return 0.0
        config.require_api_keys()
        info = self._client.get_asset_balance(asset=asset)
        return float(info["free"])

    def buy(self, symbol: str, usdt_amount: float, rsi: float = None, current_price: float = None):
        if config.DRY_RUN:
            # Use current close as simulated entry so stop-loss math works in paper mode
            entry_price = current_price
            note = "dry_run=True"
        else:
            try:
                order = self._client.order_market_buy(
                    symbol=symbol,
                    quoteOrderQty=usdt_amount,
                )
                fills = order.get("fills", [])
                entry_price = float(fills[0]["price"]) if fills else None
            except BinanceAPIException as e:
                _log.error("BUY failed for %s: %s", symbol, e)
                return
            note = f"dry_run=False"

        rsi_str = f"rsi={rsi:.1f}" if rsi is not None else "rsi=N/A"
        line = (
            f"{_now()} | BUY  | {symbol} | "
            f"price={entry_price or 'MARKET'} | usdt={usdt_amount:.2f} | "
            f"{rsi_str} | {note}"
        )
        _append_log(line)
        _log.info(line)

        self._positions[symbol] = {
            "entry_price": entry_price,
            "entry_time": _now(),
            "usdt_amount": usdt_amount,
        }
        self._save_positions()

    def sell(self, symbol: str, current_price: float = None, reason: str = "UNKNOWN"):
        position = self._positions.get(symbol)
        if position is None:
            _log.warning("SELL called for %s but no open position found", symbol)
            return

        entry_price = position.get("entry_price")

        if config.DRY_RUN:
            exit_price = current_price
            note = "dry_run=True"
        else:
            try:
                order = self._client.order_market_sell(
                    symbol=symbol,
                    quantity=self._get_held_quantity(symbol),
                )
                fills = order.get("fills", [])
                exit_price = float(fills[0]["price"]) if fills else current_price
            except BinanceAPIException as e:
                _log.error("SELL failed for %s: %s", symbol, e)
                return
            note = "dry_run=False"

        pnl_str = "N/A"
        if entry_price and exit_price:
            pnl_pct = (exit_price - entry_price) / entry_price * 100
            pnl_str = f"{pnl_pct:+.2f}%"

        line = (
            f"{_now()} | SELL | {symbol} | "
            f"price={exit_price or 'MARKET'} | entry={entry_price or 'N/A'} | "
            f"pnl={pnl_str} | reason={reason} | {note}"
        )
        _append_log(line)
        _log.info(line)

        del self._positions[symbol]
        self._save_positions()

    def _get_held_quantity(self, symbol: str) -> float:
        base_asset = symbol.replace("USDT", "")
        info = self._client.get_asset_balance(asset=base_asset)
        return float(info["free"])

    def get_open_positions(self) -> dict:
        return dict(self._positions)
