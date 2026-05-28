from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

import websockets

logger = logging.getLogger("golden_bot.ws_manager")


class BinanceWSManager:
    """
    WebSocket manager for Binance Futures (Testnet/Live).
    Handles real-time market data, order updates, and balance sync.
    """

    # Correct WebSocket endpoints for Futures market
    WS_ENDPOINTS = {
        "testnet": "wss://stream.binancefuture.com/ws",
        "live": "wss://stream.binance.com:9443/ws",
        "testnet_spot": "wss://testnet.binance.vision/ws",
        "live_spot": "wss://stream.binance.com:9443/ws",
    }

    def __init__(
            self,
            api_key: Optional[str] = None,
            api_secret: Optional[str] = None,
            env: str = "testnet",
            market: str = "futures",
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.env = env.lower()
        self.market = market.lower()

        # Select correct WebSocket URL based on env + market
        key = f"{self.env}_{self.market}" if self.market == "spot" else self.env
        self._base_url = self.WS_ENDPOINTS.get(key, self.WS_ENDPOINTS["testnet"])

        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._streams: List[str] = []
        self._handlers: Dict[str, List[Callable[[dict], Any]]] = {}
        self._listen_key: Optional[str] = None
        self._keep_running = True
        self._reconnect_delay = 1.0
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._connect_task: Optional[asyncio.Task] = None

    async def start(self, streams: List[str], handlers: Dict[str, List[Callable]]) -> None:
        """Start WebSocket connection with given streams and event handlers."""
        # Normalize stream names to lowercase (Binance requirement)
        self._streams = [s.lower() for s in streams]
        self._handlers = handlers

        # Start connection in background
        self._connect_task = asyncio.create_task(self._connect())
        self._heartbeat_task = asyncio.create_task(self._heartbeat())
        asyncio.create_task(self._listen())

        logger.info(f"🔗 WS Manager started: {self.env}/{self.market}")

    async def _connect(self) -> None:
        """Establish WebSocket connection with proper URL formatting."""
        while self._keep_running:
            try:
                # Build stream list: Binance uses '/' separator for combined streams
                stream_path = "/".join(self._streams) if self._streams else ""

                # For private streams (user data), we need a listenKey
                if self._listen_key and self.market == "futures":
                    url = f"{self._base_url}/{self._listen_key}"
                elif stream_path:
                    url = f"{self._base_url}/{stream_path}"
                else:
                    url = self._base_url

                logger.info(f"🔗 Connecting to WS: {url}")

                # Connect with proper timeouts (removed extra_headers for compatibility)
                connect_kwargs = {
                    "ping_interval": 20,
                    "ping_timeout": 10,
                    "close_timeout": 10,
                }

                # Only add headers if websockets version supports it
                try:
                    self._ws = await websockets.connect(url, **connect_kwargs,
                                                        extra_headers={"User-Agent": "GoldenBot/1.0"})
                except TypeError:
                    # Fallback for older websockets versions
                    self._ws = await websockets.connect(url, **connect_kwargs)

                self._reconnect_delay = 1.0  # Reset on successful connect
                logger.info("✅ WebSocket connected")
                return

            except websockets.exceptions.InvalidStatusCode as e:
                logger.error(f"❌ WS connection rejected: HTTP {e.status_code}")
                if e.status_code == 400:
                    logger.error("💡 Hint: Check if stream names are lowercase and endpoint matches env/market")
                await self._handle_reconnect()

            except websockets.exceptions.InvalidURI as e:
                logger.error(f"❌ Invalid WebSocket URI: {e}")
                logger.error(f"💡 Base URL: {self._base_url}, Streams: {self._streams}")
                break  # Cannot recover from invalid URI

            except Exception as e:
                logger.error(f"❌ WS connection error: {type(e).__name__}: {e}")
                await self._handle_reconnect()


    async def _handle_reconnect(self) -> None:
        """Handle reconnection with exponential backoff."""
        if not self._keep_running:
            return
        logger.warning(f"🔄 Reconnecting in {self._reconnect_delay}s...")
        await asyncio.sleep(self._reconnect_delay)
        self._reconnect_delay = min(self._reconnect_delay * 2, 60)
        # Continue loop in _connect()

    async def _listen(self) -> None:
        """Main message receiving loop."""
        while self._keep_running:
            if not self._ws or not self._ws.open:
                await asyncio.sleep(1)
                continue
            try:
                msg = await asyncio.wait_for(self._ws.recv(), timeout=30)
                data = json.loads(msg)
                self._dispatch(data)
            except asyncio.TimeoutError:
                # No message received, check connection health
                continue
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"🔌 WS connection closed: {e}")
                await self._handle_reconnect()
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse WS message: {e}")
            except Exception as e:
                logger.error(f"❌ WS receive error: {type(e).__name__}: {e}")
                await self._handle_reconnect()

    def _dispatch(self, data: dict) -> None:
        """Route incoming message to registered handlers."""
        event_type = data.get("e", "unknown")

        # Try specific handler first, then wildcard
        handlers = self._handlers.get(event_type, []) + self._handlers.get("*", [])

        for handler in handlers:
            try:
                # Handlers can be sync or async
                result = handler(data)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception as e:
                logger.error(f"❌ Handler error for '{event_type}': {e}")

    async def _heartbeat(self) -> None:
        """Send periodic pings to keep connection alive."""
        while self._keep_running:
            await asyncio.sleep(30)
            if self._ws and self._ws.open:
                try:
                    await self._ws.ping()
                except Exception:
                    pass  # Will be caught by _listen() timeout

    async def _get_listen_key(self) -> Optional[str]:
        """Generate listenKey for private user data streams (Futures)."""
        if not self.api_key or not self.api_secret:
            return None

        import hmac
        import hashlib
        import aiohttp

        try:
            # Binance Futures Testnet REST endpoint for listenKey
            base_url = "https://testnet.binancefuture.com" if self.env == "testnet" else "https://fapi.binance.com"
            url = f"{base_url}/fapi/v1/listenKey"

            timestamp = int(time.time() * 1000)
            signature = hmac.new(
                self.api_secret.encode(),
                f"timestamp={timestamp}".encode(),
                hashlib.sha256
            ).hexdigest()

            headers = {"X-MBX-APIKEY": self.api_key}
            params = {"timestamp": timestamp, "signature": signature}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get("listenKey")
                    else:
                        logger.error(f"❌ Failed to get listenKey: {resp.status}")
                        return None
        except Exception as e:
            logger.error(f"❌ Error getting listenKey: {e}")
            return None

    async def set_listen_key(self, listen_key: str) -> None:
        """Set listenKey for private user data streams."""
        self._listen_key = listen_key
        if self._ws:
            await self._ws.close()
            await self._connect()

    async def close(self) -> None:
        """Gracefully close WebSocket connection."""
        logger.info("🔌 Closing WebSocket...")
        self._keep_running = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._connect_task:
            self._connect_task.cancel()

        if self._ws and self._ws.open:
            await self._ws.close()

        logger.info("✅ WebSocket closed")

    def register_handler(self, event_type: str, handler: Callable) -> None:
        """Register a handler for a specific event type."""
        self._handlers.setdefault(event_type.lower(), []).append(handler)
        logger.debug(f"📝 Registered handler for '{event_type}'")

    def unregister_handler(self, event_type: str, handler: Callable) -> bool:
        """Unregister a specific handler."""
        handlers = self._handlers.get(event_type.lower(), [])
        if handler in handlers:
            handlers.remove(handler)
            return True
        return False