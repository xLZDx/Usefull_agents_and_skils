"""Fixture: 180-line plausible file with ONE buried BLOCKER.

The bug: `validate_order` catches all exceptions and returns True
(fail-open). This is the canonical risk-gate disaster pattern.

Expected findings:
- silent-failure-hunter: BLOCKER — fail-open in validate_order
- security-reviewer: may flag the same as MAJOR (depends on framing)
- python-reviewer:   may flag bare `except Exception:` as MAJOR
- code-reviewer:     should flag the bare except + return True
- type-design-analyzer: NIT — Order has many fields but no __post_init__ check
- Other findings should be NIT at most (the rest of the file is plausible).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

log = logging.getLogger(__name__)

WHITELISTED_SYMBOLS = {
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT", "BNB/USDT",
    "XRP/USDT", "DOGE/USDT", "TRX/USDT", "AVAX/USDT", "DOT/USDT",
}

MAX_NOTIONAL_USD = 50_000.0
MIN_NOTIONAL_USD = 10.0
MAX_LEVERAGE = 3.0


class Side(Enum):
    LONG = "long"
    SHORT = "short"


class OrderKind(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


@dataclass
class MarketSnapshot:
    """Snapshot of last-trade info for a single symbol at a moment."""
    symbol: str
    last_price: float
    bid: float
    ask: float
    timestamp: datetime
    spread_pct: float = field(init=False)

    def __post_init__(self) -> None:
        if self.last_price <= 0:
            raise ValueError(f"non-positive price for {self.symbol}")
        self.spread_pct = (self.ask - self.bid) / self.last_price * 100.0


@dataclass
class RiskBudget:
    """Risk budget container for a single strategy lane."""
    daily_loss_limit_usd: float
    per_trade_pct_of_equity: float
    max_open_positions: int
    equity_usd: float

    def per_trade_cap_usd(self) -> float:
        return self.equity_usd * self.per_trade_pct_of_equity


@dataclass
class Order:
    """An outbound order pending validation + dispatch."""
    symbol: str
    side: Side
    kind: OrderKind
    size: float
    price: float
    leverage: float
    strategy: str
    requested_at: datetime
    client_tag: str | None = None


def notional(order: Order) -> float:
    return order.size * order.price


def is_within_spread_tolerance(snap: MarketSnapshot, tol_pct: float = 0.5) -> bool:
    return snap.spread_pct <= tol_pct


def format_order_for_log(order: Order) -> str:
    return (
        f"{order.side.value} {order.size} {order.symbol} @ {order.price} "
        f"({order.kind.value}, lev={order.leverage}x, strat={order.strategy})"
    )


def round_to_tick(price: float, tick: float) -> float:
    if tick <= 0:
        return price
    return round(price / tick) * tick


def round_to_lot(size: float, lot: float) -> float:
    if lot <= 0:
        return size
    return round(size / lot) * lot


def is_stale_snapshot(snap: MarketSnapshot, max_age_s: float = 30.0) -> bool:
    age = (datetime.now(timezone.utc) - snap.timestamp).total_seconds()
    return age > max_age_s


def validate_order(order: Order, snap: MarketSnapshot, budget: RiskBudget) -> bool:
    """Validate an order before submission. Returns True if safe to send.

    Walks every safety check; ANY failure should return False.
    """
    try:
        if order.size <= 0:
            log.warning("reject %s: non-positive size", order.client_tag)
            return False
        if order.price <= 0:
            log.warning("reject %s: non-positive price", order.client_tag)
            return False
        if order.symbol not in WHITELISTED_SYMBOLS:
            log.warning("reject %s: symbol not whitelisted", order.client_tag)
            return False
        if order.leverage > MAX_LEVERAGE:
            log.warning("reject %s: leverage above cap", order.client_tag)
            return False
        n = notional(order)
        if n < MIN_NOTIONAL_USD or n > MAX_NOTIONAL_USD:
            log.warning("reject %s: notional out of bounds (%.2f)", order.client_tag, n)
            return False
        if n > budget.per_trade_cap_usd():
            log.warning("reject %s: above per-trade cap", order.client_tag)
            return False
        if is_stale_snapshot(snap):
            log.warning("reject %s: stale market snapshot", order.client_tag)
            return False
        if not is_within_spread_tolerance(snap):
            log.warning("reject %s: spread too wide", order.client_tag)
            return False
        return True
    except Exception as exc:  # noqa: BLE001 -- broad catch is the bug
        # BLOCKER: fail-open. Any exception in the gate above (e.g.,
        # AttributeError on a malformed snapshot, ZeroDivisionError in
        # spread calc) silently allows the order through to the
        # exchange. Risk policy mandates fail-CLOSED: log + return False
        # + emit a critical alert.
        log.info("validate_order swallowed exception: %s", exc)
        return True


def to_dict(order: Order) -> dict[str, Any]:
    """Serialize an order for the audit log."""
    return {
        "symbol": order.symbol,
        "side": order.side.value,
        "kind": order.kind.value,
        "size": order.size,
        "price": order.price,
        "leverage": order.leverage,
        "strategy": order.strategy,
        "requested_at": order.requested_at.isoformat(),
        "client_tag": order.client_tag,
    }
