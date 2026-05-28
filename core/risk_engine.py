"""
core/risk_engine.py — Phase 4: Production Risk Management
Position sizing, stop-loss, take-profit, drawdown limits, correlation checks.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set

import numpy as np

from core.security import AuditLogger, AuditAction

logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","mod":"%(name)s","msg":"%(message)s"}',
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("golden_bot.risk_engine")


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskConfig:
    """Risk management configuration parameters."""
    max_loss_usd: float = 100.0
    max_loss_per_trade_usd: float = 10.0
    risk_per_trade_pct: float = 1.0
    max_parallel_trades: int = 3
    max_position_size_usd: float = 1000.0
    stop_loss_pct: float = 2.0
    take_profit_pct: float = 4.0
    trailing_stop_pct: float = 1.0
    correlation_threshold: float = 0.8
    max_drawdown_pct: float = 10.0
    min_position_size_usd: float = 1.0
    max_leverage: int = 125
    cooldown_between_trades_sec: int = 60


@dataclass
class Position:
    """Represents an open position for risk calculations."""
    symbol: str
    side: str  # "LONG" or "SHORT"
    entry_price: float
    quantity: float
    leverage: int
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    opened_at: datetime = field(default_factory=datetime.now)
    trade_id: Optional[str] = None

    @property
    def notional_value(self) -> float:
        """Calculate notional value (entry_price * quantity * leverage)."""
        return self.entry_price * self.quantity * self.leverage

    def unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized PnL."""
        if self.side == "LONG":
            return (current_price - self.entry_price) * self.quantity * self.leverage
        else:
            return (self.entry_price - current_price) * self.quantity * self.leverage

    def pnl_pct(self, current_price: float) -> float:
        """Calculate PnL as percentage of entry."""
        if self.side == "LONG":
            return (current_price - self.entry_price) / self.entry_price * 100
        else:
            return (self.entry_price - current_price) / self.entry_price * 100


class PositionSizer:
    """
    Phase 4: Calculate optimal position sizes based on risk parameters.

    Supports multiple sizing strategies:
    - Fixed fractional (risk % of equity)
    - Kelly criterion (optimal growth)
    - Volatility-adjusted (ATR-based)
    - Fixed notional (fixed USD amount)
    """

    def __init__(self, config: RiskConfig):
        self.config = config

    def calculate_position_size(
            self,
            equity: float,
            entry_price: float,
            stop_loss_price: Optional[float] = None,
            risk_pct: Optional[float] = None,
            strategy: str = "fixed_fractional",
            atr: Optional[float] = None,
            kelly_fraction: float = 0.25,  # Fractional Kelly for safety
    ) -> float:
        """
        Calculate optimal position size based on risk parameters.

        Args:
            equity: Current account equity in USD
            entry_price: Entry price of the asset
            stop_loss_price: Stop loss price (for risk-based sizing)
            risk_pct: Risk percentage per trade (default: config.risk_per_trade_pct)
            strategy: Sizing strategy: "fixed_fractional", "kelly", "atr", "fixed"
            atr: Average True Range for volatility-adjusted sizing
            kelly_fraction: Fraction of Kelly bet (0.25 = quarter-Kelly)

        Returns:
            Position size in base asset units (e.g., BTC for BTCUSDT)
        """
        risk_pct = risk_pct or self.config.risk_per_trade_pct / 100

        if strategy == "fixed_fractional":
            return self._fixed_fractional(equity, entry_price, stop_loss_price, risk_pct)
        elif strategy == "kelly":
            return self._kelly_criterion(equity, entry_price, stop_loss_price, risk_pct, kelly_fraction)
        elif strategy == "atr":
            return self._atr_based(equity, entry_price, atr, risk_pct)
        elif strategy == "fixed":
            return self._fixed_notional(equity, entry_price)
        else:
            logger.warning(f"⚠️ Unknown sizing strategy: {strategy}, using fixed_fractional")
            return self._fixed_fractional(equity, entry_price, stop_loss_price, risk_pct)

    def _fixed_fractional(
            self,
            equity: float,
            entry_price: float,
            stop_loss_price: Optional[float],
            risk_pct: float,
    ) -> float:
        """Fixed fractional position sizing: risk X% of equity per trade."""
        if entry_price <= 0:
            return 0.0

        risk_amount = equity * risk_pct

        if stop_loss_price and stop_loss_price > 0:
            # Size based on stop loss distance
            price_distance = abs(entry_price - stop_loss_price)
            if price_distance <= 0:
                return 0.0
            quantity = risk_amount / price_distance
        else:
            # Fallback: size based on fixed % of equity
            quantity = (equity * risk_pct) / entry_price

        # Apply limits
        quantity = max(0, min(
            quantity,
            self.config.max_position_size_usd / entry_price
        ))

        # Ensure minimum position size
        if quantity * entry_price < self.config.min_position_size_usd:
            return 0.0

        return quantity

    def _kelly_criterion(
            self,
            equity: float,
            entry_price: float,
            stop_loss_price: Optional[float],
            risk_pct: float,
            kelly_fraction: float,
    ) -> float:
        """
        Kelly criterion position sizing: f* = (bp - q) / b
        Where b = odds, p = win probability, q = loss probability

        Simplified for trading: use historical win rate and avg win/loss ratio.
        """
        # Default assumptions (should be overridden with actual stats)
        win_rate = 0.55  # Historical win rate
        avg_win = 2.0  # Avg win as multiple of risk
        avg_loss = 1.0  # Avg loss as multiple of risk

        # Kelly fraction: f* = (p * b - q) / b
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - p
        kelly_pct = (p * b - q) / b if b > 0 else 0

        # Apply fractional Kelly for safety
        effective_risk_pct = risk_pct * kelly_fraction * max(0, kelly_pct)

        return self._fixed_fractional(equity, entry_price, stop_loss_price, effective_risk_pct)

    def _atr_based(
            self,
            equity: float,
            entry_price: float,
            atr: Optional[float],
            risk_pct: float,
    ) -> float:
        """ATR-based position sizing: size inversely proportional to volatility."""
        if atr is None or atr <= 0:
            # Fallback to fixed fractional if ATR not available
            return self._fixed_fractional(equity, entry_price, None, risk_pct)

        # Stop loss at 2x ATR (common practice)
        stop_distance = atr * 2
        risk_amount = equity * risk_pct

        quantity = risk_amount / stop_distance

        # Apply limits
        quantity = max(0, min(
            quantity,
            self.config.max_position_size_usd / entry_price
        ))

        if quantity * entry_price < self.config.min_position_size_usd:
            return 0.0

        return quantity

    def _fixed_notional(self, equity: float, entry_price: float) -> float:
        """Fixed notional sizing: always trade same USD amount."""
        notional = min(
            self.config.max_position_size_usd,
            equity * 0.1  # Never use more than 10% of equity
        )
        return notional / entry_price if entry_price > 0 else 0.0

    def validate_position_size(
            self,
            quantity: float,
            entry_price: float,
            leverage: int,
            equity: float,
    ) -> tuple[bool, str]:
        """Validate position size against risk limits."""
        notional = quantity * entry_price * leverage

        if notional > self.config.max_position_size_usd:
            return False, f"Notional ${notional:.2f} exceeds max ${self.config.max_position_size_usd}"

        if leverage > self.config.max_leverage:
            return False, f"Leverage {leverage}x exceeds max {self.config.max_leverage}x"

        if quantity * entry_price < self.config.min_position_size_usd:
            return False, f"Position ${quantity * entry_price:.2f} below minimum ${self.config.min_position_size_usd}"

        return True, "OK"


class RiskManager:
    """
    Phase 4: Comprehensive risk management engine.

    Features:
    - Real-time PnL monitoring
    - Stop-loss and take-profit enforcement
    - Drawdown limits and circuit breakers
    - Correlation checks to prevent overexposure
    - Position limits and cooldowns
    - Risk level assessment and alerts
    """

    def __init__(
            self,
            config: RiskConfig,
            equity: float,
            audit: Optional[AuditLogger] = None,
    ):
        self.config = config
        self._equity = equity
        self._initial_equity = equity
        self._audit = audit
        self._positions: Dict[str, Position] = {}
        self._closed_trades: List[Dict] = []
        self._last_trade_time: Dict[str, datetime] = {}
        self._drawdown_high: float = equity
        self._circuit_breaker_active = False
        self._circuit_breaker_until: Optional[datetime] = None

    def update_equity(self, new_equity: float) -> None:
        """Update current equity and track drawdown."""
        self._equity = new_equity
        self._drawdown_high = max(self._drawdown_high, new_equity)

        # Check circuit breaker
        if self._check_circuit_breaker():
            logger.critical("🛑 Circuit breaker activated!")
            self._circuit_breaker_active = True
            self._circuit_breaker_until = datetime.now() + timedelta(hours=1)

    @property
    def equity(self) -> float:
        return self._equity

    @property
    def drawdown_pct(self) -> float:
        """Calculate current drawdown as percentage."""
        if self._drawdown_high <= 0:
            return 0.0
        return (self._drawdown_high - self._equity) / self._drawdown_high * 100

    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker should activate."""
        # Activate if drawdown exceeds threshold
        if self.drawdown_pct >= self.config.max_drawdown_pct:
            return True

        # Activate if max loss reached
        if self._equity < self._initial_equity - self.config.max_loss_usd:
            return True

        return False

    def can_open_position(self, symbol: str, side: str) -> tuple[bool, str]:
        """
        Check if a new position can be opened.

        Returns:
            (can_open: bool, reason: str)
        """
        # Check circuit breaker
        if self._circuit_breaker_active:
            if self._circuit_breaker_until and datetime.now() < self._circuit_breaker_until:
                return False, f"Circuit breaker active until {self._circuit_breaker_until}"
            else:
                self._circuit_breaker_active = False

        # Check max parallel trades
        if len(self._positions) >= self.config.max_parallel_trades:
            return False, f"Max parallel trades ({self.config.max_parallel_trades}) reached"

        # Check cooldown
        last_trade = self._last_trade_time.get(symbol)
        if last_trade:
            cooldown = (datetime.now() - last_trade).total_seconds()
            if cooldown < self.config.cooldown_between_trades_sec:
                return False, f"Cooldown: {self.config.cooldown_between_trades_sec - cooldown:.0f}s remaining"

        # Check correlation (prevent overexposure to correlated assets)
        if not self._check_correlation(symbol, side):
            return False, "Correlation limit exceeded"

        # Check equity
        if self._equity < self.config.min_position_size_usd * 2:
            return False, "Insufficient equity for new position"

        return True, "OK"

    def _check_correlation(self, symbol: str, side: str) -> bool:
        """
        Check if opening this position would exceed correlation limits.

        Simplified: prevent multiple positions on same side for correlated pairs.
        In production: use actual correlation matrix from historical data.
        """
        # Define correlated pairs (simplified)
        correlated = {
            "BTCUSDT": ["ETHUSDT", "SOLUSDT", "BNBUSDT"],
            "ETHUSDT": ["BTCUSDT", "SOLUSDT", "MATICUSDT"],
            "SOLUSDT": ["BTCUSDT", "ETHUSDT", "AVAXUSDT"],
        }

        same_side_correlated = 0
        for corr_symbol in correlated.get(symbol, []):
            if corr_symbol in self._positions:
                if self._positions[corr_symbol].side == side:
                    same_side_correlated += 1

        # Allow max 2 correlated positions on same side
        return same_side_correlated < 2

    def calculate_position_size(
            self,
            symbol: str,
            side: str,
            entry_price: float,
            stop_loss_price: Optional[float] = None,
            leverage: int = 1,
            strategy: str = "fixed_fractional",
    ) -> tuple[Optional[float], str]:
        """
        Calculate and validate position size for a new trade.

        Returns:
            (quantity: float or None, message: str)
        """
        # Check if position can be opened
        can_open, reason = self.can_open_position(symbol, side)
        if not can_open:
            return None, reason

        # Calculate size using PositionSizer
        sizer = PositionSizer(self.config)
        quantity = sizer.calculate_position_size(
            equity=self._equity,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            strategy=strategy,
        )

        if quantity <= 0:
            return None, "Position size calculation returned 0"

        # Validate against limits
        valid, msg = sizer.validate_position_size(
            quantity=quantity,
            entry_price=entry_price,
            leverage=leverage,
            equity=self._equity,
        )

        if not valid:
            return None, msg

        return quantity, "OK"

    def add_position(
            self,
            trade_id: str,
            symbol: str,
            side: str,
            entry_price: float,
            quantity: float,
            leverage: int,
            stop_loss: Optional[float] = None,
            take_profit: Optional[float] = None,
    ) -> bool:
        """Add a new position to risk tracking."""
        if trade_id in self._positions:
            logger.warning(f"⚠️ Position {trade_id} already exists")
            return False

        position = Position(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            leverage=leverage,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trade_id=trade_id,
        )

        self._positions[trade_id] = position
        self._last_trade_time[symbol] = datetime.now()

        if self._audit:
            self._audit.log(
                AuditAction.TRADE_EXECUTION,
                symbol,
                "risk_manager",
                "127.0.0.1",
                "success",
                f"Position opened: {side} {quantity} {symbol} @ ${entry_price:.2f}"
            )

        logger.info(f"✅ Position added: {trade_id} {side} {symbol}")
        return True

    def remove_position(self, trade_id: str, realized_pnl: float = 0.0) -> bool:
        """Remove a closed position from risk tracking."""
        if trade_id not in self._positions:
            return False

        position = self._positions.pop(trade_id)

        # Track closed trade stats
        self._closed_trades.append({
            "trade_id": trade_id,
            "symbol": position.symbol,
            "side": position.side,
            "entry_price": position.entry_price,
            "exit_price": position.entry_price + (realized_pnl / position.quantity / position.leverage),
            "pnl": realized_pnl,
            "closed_at": datetime.now(),
        })

        # Keep only last 100 closed trades for stats
        if len(self._closed_trades) > 100:
            self._closed_trades = self._closed_trades[-100:]

        if self._audit:
            self._audit.log(
                AuditAction.TRADE_EXECUTION,
                position.symbol,
                "risk_manager",
                "127.0.0.1",
                "success",
                f"Position closed: {trade_id} PnL: ${realized_pnl:.2f}"
            )

        logger.info(f"✅ Position removed: {trade_id} PnL: ${realized_pnl:.2f}")
        return True

    def check_stop_loss(self, trade_id: str, current_price: float) -> Optional[str]:
        """Check if stop loss should be triggered. Returns trade_id if triggered."""
        if trade_id not in self._positions:
            return None

        position = self._positions[trade_id]

        if position.stop_loss is None:
            return None

        triggered = False
        if position.side == "LONG" and current_price <= position.stop_loss:
            triggered = True
        elif position.side == "SHORT" and current_price >= position.stop_loss:
            triggered = True

        if triggered:
            logger.info(f"🛑 Stop loss triggered: {trade_id} at ${current_price:.2f}")
            return trade_id

        return None

    def check_take_profit(self, trade_id: str, current_price: float) -> Optional[str]:
        """Check if take profit should be triggered. Returns trade_id if triggered."""
        if trade_id not in self._positions:
            return None

        position = self._positions[trade_id]

        if position.take_profit is None:
            return None

        triggered = False
        if position.side == "LONG" and current_price >= position.take_profit:
            triggered = True
        elif position.side == "SHORT" and current_price <= position.take_profit:
            triggered = True

        if triggered:
            logger.info(f"✅ Take profit triggered: {trade_id} at ${current_price:.2f}")
            return trade_id

        return None

    def update_trailing_stop(self, trade_id: str, current_price: float) -> Optional[float]:
        """Update trailing stop loss. Returns new stop price if updated."""
        if trade_id not in self._positions:
            return None

        position = self._positions[trade_id]

        if position.stop_loss is None or self.config.trailing_stop_pct <= 0:
            return None

        trailing_distance = position.entry_price * (self.config.trailing_stop_pct / 100)

        new_stop = None
        if position.side == "LONG":
            # For long: trailing stop moves up with price
            potential_stop = current_price - trailing_distance
            if position.stop_loss is None or potential_stop > position.stop_loss:
                new_stop = potential_stop
        else:
            # For short: trailing stop moves down with price
            potential_stop = current_price + trailing_distance
            if position.stop_loss is None or potential_stop < position.stop_loss:
                new_stop = potential_stop

        if new_stop is not None:
            position.stop_loss = new_stop
            logger.debug(f"🔄 Trailing stop updated: {trade_id} -> ${new_stop:.2f}")
            return new_stop

        return None

    def get_risk_level(self) -> RiskLevel:
        """Assess current overall risk level."""
        drawdown = self.drawdown_pct

        if drawdown >= self.config.max_drawdown_pct * 0.8:
            return RiskLevel.CRITICAL
        elif drawdown >= self.config.max_drawdown_pct * 0.5:
            return RiskLevel.HIGH
        elif drawdown >= self.config.max_drawdown_pct * 0.2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def get_portfolio_exposure(self) -> Dict[str, float]:
        """Calculate exposure by symbol and side."""
        exposure = {}
        for position in self._positions.values():
            key = f"{position.symbol}_{position.side}"
            exposure[key] = exposure.get(key, 0) + position.notional_value
        return exposure

    def get_stats(self) -> Dict[str, Any]:
        """Get current risk statistics."""
        closed = [t for t in self._closed_trades if t.get("pnl") is not None]

        return {
            "equity": self._equity,
            "initial_equity": self._initial_equity,
            "drawdown_pct": self.drawdown_pct,
            "risk_level": self.get_risk_level().value,
            "open_positions": len(self._positions),
            "closed_trades": len(closed),
            "total_pnl": sum(t.get("pnl", 0) for t in closed),
            "win_rate": (
                sum(1 for t in closed if t.get("pnl", 0) > 0) / len(closed) * 100
                if closed else 0
            ),
            "circuit_breaker": self._circuit_breaker_active,
            "exposure": self.get_portfolio_exposure(),
        }

    def reset(self) -> None:
        """Reset risk manager state (for testing or restart)."""
        self._positions.clear()
        self._closed_trades.clear()
        self._drawdown_high = self._equity
        self._circuit_breaker_active = False
        self._circuit_breaker_until = None
        logger.info("🔄 Risk manager reset")