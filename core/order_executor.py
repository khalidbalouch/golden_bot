"""
core/order_executor.py — Phase 3: Order Execution Engine
Place, manage, and track orders on Binance Futures (Testnet/Live).
"""
from __future__ import annotations

import asyncio
import hmac
import hashlib
import time
import logging
from enum import Enum
from typing import Optional, Dict, Any, List
from pathlib import Path

import aiohttp
import requests  # For Windows-compatible sync fallback

from core.security import AuditLogger, AuditAction

logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","mod":"%(name)s","msg":"%(message)s"}',
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("golden_bot.order_executor")


class OrderSide(Enum):
    LONG = "BUY"
    SHORT = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_MARKET = "STOP_MARKET"
    STOP_LIMIT = "STOP_LIMIT"
    TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"


class OrderStatus(Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class OrderExecutor:
    """
    Phase 3: Execute orders on Binance Futures with proper error handling,
    retry logic, and audit logging.
    """

    def __init__(
            self,
            api_key: str,
            api_secret: str,
            base_url: str,
            dry_run: bool = True,
            audit: Optional[AuditLogger] = None,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.dry_run = dry_run
        self.audit = audit
        self._session: Optional[aiohttp.ClientSession] = None
        self._order_cache: Dict[str, Dict] = {}

        # Windows DNS fix
        import os
        os.environ["AIOHTTP_NO_AIODNS"] = "1"

    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession(
            headers={"X-MBX-APIKEY": self.api_key},
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for Binance API."""
        query_string = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return hmac.new(
            self.api_secret.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()

    def _sync_request(
            self,
            method: str,
            endpoint: str,
            params: Optional[Dict] = None,
            data: Optional[Dict] = None,
            signed: bool = False,
    ) -> Dict:
        """
        Sync HTTP request using requests (for Windows compatibility).
        Runs in thread pool to avoid blocking event loop.
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"X-MBX-APIKEY": self.api_key}

        if params is None:
            params = {}

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._generate_signature(params)

        try:
            if method.upper() == "GET":
                resp = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                resp = requests.post(url, headers=headers, params=params, json=data, timeout=30)
            elif method.upper() == "DELETE":
                resp = requests.delete(url, headers=headers, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            resp.raise_for_status()
            return resp.json()

        except requests.RequestException as e:
            logger.error(f"❌ HTTP error: {e}")
            raise

    async def _request(
            self,
            method: str,
            endpoint: str,
            params: Optional[Dict] = None,
            data: Optional[Dict] = None,
            signed: bool = False,
    ) -> Dict:
        """Async HTTP request with fallback to sync for Windows."""
        if self.dry_run:
            logger.info(f"🧪 [DRY RUN] {method} {endpoint} params={params}")
            return {"code": 200, "msg": "OK", "dry_run": True}

        # Try async first
        try:
            if not self._session:
                self._session = aiohttp.ClientSession(
                    headers={"X-MBX-APIKEY": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=30)
                )

            if signed:
                params = params or {}
                params["timestamp"] = int(time.time() * 1000)
                params["signature"] = self._generate_signature(params)

            async with self._session.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    params=params if method == "GET" else None,
                    json=data if method == "POST" else None,
            ) as resp:
                return await resp.json()

        except Exception as e:
            logger.warning(f"⚠️ Async request failed, falling back to sync: {e}")
            # Fallback to sync request in thread pool
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None,
                lambda: self._sync_request(method, endpoint, params, data, signed)
            )

    async def place_order(
            self,
            symbol: str,
            side: OrderSide,
            order_type: OrderType,
            quantity: float,
            price: Optional[float] = None,
            leverage: int = 1,
            sl_price: Optional[float] = None,
            tp_price: Optional[float] = None,
            client_order_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Place a new order on Binance Futures.

        Returns:
            trade_id (order ID) if successful, None if failed
        """
        if self.dry_run:
            trade_id = f"DRY_{int(time.time() * 1000)}"
            logger.info(f"🧪 [DRY RUN] Order placed: {trade_id} {side.value} {symbol}")
            if self.audit:
                self.audit.log(
                    AuditAction.TRADE_EXECUTION,
                    symbol,
                    "order_executor",
                    "127.0.0.1",
                    "success",
                    f"[DRY RUN] {side.value} {quantity} {symbol} @ {price or 'MARKET'}"
                )
            return trade_id

        try:
            # Set leverage first if specified
            if leverage > 1:
                await self._set_leverage(symbol, leverage)

            # Prepare order params
            params = {
                "symbol": symbol.upper(),
                "side": side.value,
                "type": order_type.value,
                "quantity": quantity,
                "newClientOrderId": client_order_id or f"gb_{int(time.time() * 1000)}",
            }

            if price and order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT, OrderType.TAKE_PROFIT_LIMIT]:
                params["price"] = price

            if sl_price:
                params["stopPrice"] = sl_price

            if tp_price:
                params["priceProtect"] = "true"

            # Place order
            result = await self._request("POST", "/fapi/v1/order", params=params, signed=True)

            if result.get("code") == 200 or "orderId" in result:
                trade_id = str(result.get("orderId") or result.get("clientOrderId"))
                self._order_cache[trade_id] = {
                    "symbol": symbol,
                    "side": side.value,
                    "quantity": quantity,
                    "price": price,
                    "status": "NEW",
                }
                logger.info(f"✅ Order placed: {trade_id} {side.value} {symbol}")
                if self.audit:
                    self.audit.log(
                        AuditAction.TRADE_EXECUTION,
                        symbol,
                        "order_executor",
                        "127.0.0.1",
                        "success",
                        f"Order placed: {trade_id} {side.value} {quantity} {symbol}"
                    )
                return trade_id
            else:
                logger.error(f"❌ Order failed: {result}")
                return None

        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
            return None

    async def _set_leverage(self, symbol: str, leverage: int) -> None:
        """Set leverage for a symbol."""
        params = {
            "symbol": symbol.upper(),
            "leverage": leverage,
        }
        await self._request("POST", "/fapi/v1/leverage", params=params, signed=True)

    async def close_position(self, trade_id: str, quantity: Optional[float] = None) -> bool:
        """Close an existing position by placing opposite order."""
        if trade_id not in self._order_cache:
            logger.warning(f"⚠️ Trade {trade_id} not found in cache")
            return False

        order = self._order_cache[trade_id]
        symbol = order["symbol"]
        side = OrderSide.SHORT if order["side"] == "BUY" else OrderSide.LONG
        qty = quantity or order["quantity"]

        # Place closing order
        result = await self.place_order(
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=qty,
        )

        if result:
            order["status"] = "CLOSING"
            logger.info(f"✅ Position closing: {trade_id}")
            return True
        return False

    async def cancel_order(self, trade_id: str, symbol: str) -> bool:
        """Cancel an open order."""
        params = {
            "symbol": symbol.upper(),
            "origClientOrderId": trade_id,
        }
        result = await self._request("DELETE", "/fapi/v1/order", params=params, signed=True)

        if result.get("code") == 200 or "status" in result:
            if trade_id in self._order_cache:
                self._order_cache[trade_id]["status"] = "CANCELED"
            logger.info(f"✅ Order canceled: {trade_id}")
            return True
        return False

    async def get_order_status(self, trade_id: str, symbol: str) -> Optional[Dict]:
        """Get current status of an order."""
        params = {
            "symbol": symbol.upper(),
            "origClientOrderId": trade_id,
        }
        result = await self._request("GET", "/fapi/v1/order", params=params, signed=True)

        if "status" in result:
            status = OrderStatus(result.get("status", "NEW"))
            if trade_id in self._order_cache:
                self._order_cache[trade_id]["status"] = status.value
            return {
                "trade_id": trade_id,
                "symbol": symbol,
                "status": status.value,
                "filled_qty": result.get("executedQty", 0),
                "avg_price": result.get("avgPrice", 0),
            }
        return None

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open orders, optionally filtered by symbol."""
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()

        result = await self._request("GET", "/fapi/v1/openOrders", params=params, signed=True)

        if isinstance(result, list):
            return [
                {
                    "trade_id": o.get("clientOrderId"),
                    "symbol": o.get("symbol"),
                    "side": o.get("side"),
                    "type": o.get("type"),
                    "quantity": float(o.get("origQty", 0)),
                    "price": float(o.get("price", 0)),
                    "status": o.get("status"),
                }
                for o in result
            ]
        return []

    async def get_account_balance(self) -> Dict[str, float]:
        """Get account balance for all assets."""
        result = await self._request("GET", "/fapi/v2/account", signed=True)

        balances = {}
        for asset in result.get("assets", []):
            balances[asset["asset"]] = float(asset.get("walletBalance", 0))
        return balances

    def get_cached_order(self, trade_id: str) -> Optional[Dict]:
        """Get order from local cache."""
        return self._order_cache.get(trade_id)

    def clear_cache(self) -> None:
        """Clear order cache."""
        self._order_cache.clear()