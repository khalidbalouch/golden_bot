"""
utils/web_monitor.py — Professional Flask web dashboard with SSE real-time updates
"""
import json
import logging
import queue
import re
import threading
import time
from typing import Any, Dict, List, Optional

from flask import Flask, Response, make_response, request

logger = logging.getLogger("WEB_MON")

# =============================================================================
# SHARED STATE (Thread-safe)
# =============================================================================
_state: Dict[str, Any] = {
    "balance": 0.0,
    "peak_bal": 0.0,
    "daily_pnl": 0.0,
    "scan_count": 0,
    "signal_count": 0,
    "start_time": time.time(),
    "session_start": 0.0,
    "env": "TESTNET",
    "market": "FUTURES",
    "bot_name": "GOLDEN BOT",
    "api_key_file": "",
    "max_loss_usd": 150.0,
    "leverage": 5,
    "trades": [],
    "closed_trades": [],
    "prices": {},
    "regimes": {},
    "paused": False,
    "offline": False,
    "uptime_min": "0",
    "open_pnl": 0.0,
    "net_pnl": 0.0,
    "realized_pnl": 0.0,
    "wins": 0,
    "losses": 0,
    "active_count": 0,
    "closed_count": 0,
    "session_loss": 0.0,
    "logs": [],
    "use_ml": False,
    "score_gate": 45.0,
    "theme": "dark_blue",
    "symbols": [],
    "win_rate": 0.0,
    "alpha": {
        "cvd": 0,
        "ob_imbalance": 0,
        "funding_alpha_bps": 0,
        "liq_proximity": 0,
        "oi_momentum": 0,
    },
}
_state_lock = threading.Lock()
_sse_queues: List[queue.Queue] = []
_sse_lock = threading.Lock()
_server_thread = None
_token = "cl_bot"
_engine_ref = None
_port = 8080


# =============================================================================
# PUBLIC API
# =============================================================================
def register_engine(engine) -> None:
    """Register the main bot engine for command routing."""
    global _engine_ref
    _engine_ref = engine


def add_log(msg: str) -> None:
    """Add a log entry to the shared state and push to SSE clients."""
    clean = re.sub(r"\[/?[^\]]*\]", "", str(msg))
    ts = time.strftime("%H:%M:%S")
    entry = {"ts": ts, "msg": clean}
    with _state_lock:
        _state["logs"].append(entry)
        if len(_state["logs"]) > 200:
            _state["logs"] = _state["logs"][-200:]
    _push_sse()


def update_state(
        engine,
        balance: float,
        peak_bal: float,
        daily_pnl: float,
        scan_count: int,
        signal_count: int,
        start_time: float,
        session_start: float,
        active_trades: list,
        closed_trades: list,
        prices: dict,
        regimes: dict,
        paused: bool,
        offline: bool,
        config,
        features: Optional[dict] = None,
) -> None:
    """Update shared state with latest bot metrics and push to SSE clients."""
    try:

        def fp(p):
            """Format price/number for display."""
            if p is None:
                return "0"
            p = float(p)
            if p < 1:
                return f"{p:.6f}"
            if p < 100:
                return f"{p:.4f}"
            return f"{p:,.2f}"

        # Calculate PnL metrics
        open_pnl = sum(
            t.unrealized_pnl(prices.get(t.symbol, t.entry_price))
            for t in active_trades
            if hasattr(t, "unrealized_pnl")
        )
        realized = sum(getattr(t, "realized_pnl", 0) for t in closed_trades)
        net_pnl = realized + open_pnl

        # Calculate win/loss stats
        wins = sum(1 for t in closed_trades if getattr(t, "realized_pnl", 0) > 0)
        losses = len(closed_trades) - wins
        wr = (wins / len(closed_trades) * 100) if closed_trades else 0.0
        uptime = (time.time() - start_time) / 60

        # Serialize active trades for JSON
        trade_list = []
        for t in active_trades:
            cp = prices.get(t.symbol, t.entry_price)
            upnl = t.unrealized_pnl(cp) if hasattr(t, "unrealized_pnl") else 0
            ppct = t.pnl_pct(cp) if hasattr(t, "pnl_pct") else 0
            age = (time.time() - getattr(t, "open_time", time.time())) / 60

            # Build flags string safely
            flags = ""
            src = getattr(t, "source", None)
            if src:
                src_val = src.value if hasattr(src, "value") else str(src)
                if src_val.upper() == "ML":
                    flags += "ML "
            if getattr(t, "breakeven_moved", False):
                flags += "BE "
            if getattr(t, "trailing_active", False):
                flags += "TR "

            # Handle direction enum or string
            direction = getattr(t, "direction", "")
            if hasattr(direction, "value"):
                direction = direction.value

            trade_list.append(
                {
                    "id": getattr(t, "trade_id", "?"),
                    "symbol": t.symbol,
                    "direction": str(direction).upper(),
                    "market": str(getattr(t, "market", "FUTURES")),
                    "entry": fp(t.entry_price),
                    "current": fp(cp),
                    "sl": fp(t.sl_price),
                    "tp1": fp(t.tp1_price),
                    "pnl": f"{upnl:+.4f}",
                    "pnl_pct": f"{ppct:+.2f}%",
                    "pnl_pos": upnl >= 0,
                    "score": f"{getattr(t, 'score', 0):.1f}",
                    "flags": flags.strip(),
                    "age": f"{age:.0f}m",
                    "lev": f"{getattr(t, 'leverage', 1)}x",
                }
            )

        # Serialize closed trades (last 20)
        closed_list = []
        for t in list(closed_trades)[-20:]:
            pnl = getattr(t, "realized_pnl", 0)
            age = (getattr(t, "close_time", time.time()) - getattr(t, "open_time", time.time())) / 60
            source = getattr(t, "source", "")
            if hasattr(source, "value"):
                source = source.value

            closed_list.append(
                {
                    "id": getattr(t, "trade_id", "?"),
                    "symbol": t.symbol,
                    "direction": str(getattr(t, "direction", "")).upper(),
                    "entry": fp(t.entry_price),
                    "pnl": f"{pnl:+.4f}",
                    "pnl_pos": pnl >= 0,
                    "age": f"{age:.0f}m",
                    "source": str(source),
                }
            )

        # Update shared state atomically
        with _state_lock:
            _state.update(
                {
                    "balance": round(balance, 4),
                    "peak_bal": round(peak_bal, 4),
                    "daily_pnl": round(daily_pnl, 4),
                    "scan_count": scan_count,
                    "signal_count": signal_count,
                    "start_time": start_time,
                    "session_start": session_start,
                    "env": getattr(config, "env", "TESTNET"),
                    "market": getattr(config, "market", "FUTURES"),
                    "api_key_file": getattr(config, "_key_file", ""),
                    "max_loss_usd": getattr(config, "max_loss_usd", 150.0),
                    "leverage": getattr(config, "leverage", 5),
                    "score_gate": getattr(config, "score_gate", 45.0),
                    "use_ml": getattr(config, "use_ml", False),
                    "symbols": list(prices.keys()),
                    "trades": trade_list,
                    "closed_trades": closed_list,
                    "prices": {k: fp(v) for k, v in prices.items()},
                    "regimes": regimes,
                    "paused": paused,
                    "offline": offline,
                    "uptime_min": f"{uptime:.0f}",
                    "open_pnl": round(open_pnl, 4),
                    "net_pnl": round(net_pnl, 4),
                    "realized_pnl": round(realized, 4),
                    "wins": wins,
                    "losses": losses,
                    "win_rate": round(wr, 1),
                    "active_count": len(active_trades),
                    "closed_count": len(closed_trades),
                    "session_loss": round(session_start - balance, 4),
                    "dry_run": getattr(config, "dry_run", True),
                    "theme": getattr(config, "dashboard_theme", "dark_blue"),
                    "alpha": features or {},
                }
            )
        _push_sse()

    except Exception as e:
        logger.debug(f"update_state error: {e}")


def _push_sse() -> None:
    """Push current state to all connected SSE clients."""
    with _state_lock:
        payload = json.dumps(_state)
    msg = f"data: {payload}\n\n"
    with _sse_lock:
        dead = []
        for q in _sse_queues:
            try:
                q.put_nowait(msg)
            except Exception:
                dead.append(q)
        for q in dead:
            if q in _sse_queues:
                _sse_queues.remove(q)


# =============================================================================
# HTML DASHBOARD TEMPLATE
# =============================================================================
_HTML = r"""<!DOCTYPE html>
<html>
<head>
    <title>Golden Bot Dashboard</title>
    <style>
        body{font-family:monospace;background:#050a0f;color:#cfcfcf;padding:20px;margin:0;}
        h1,h2,h3{color:#00d4ff;margin:0 0 10px 0;}
        .grid{display:grid;grid-template-columns:1fr 1fr;gap:15px;}
        .card{background:#0a1520;padding:15px;border:1px solid #00d4ff44;border-radius:8px;}
        .metric{display:flex;justify-content:space-between;margin:5px 0;}
        .val.pos{color:#00ff88;}.val.neg{color:#ff4444;}.val.warn{color:#ffd700;}
        .trade-row,.log-row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #ffffff11;}
    </style>
</head>
<body>
    <h1>🟡 GOLDEN BOT LIVE</h1>
    <div class="grid">
        <div class="card">
            <h2>Account</h2>
            <div class="metric"><span>Wallet:</span><span id="bal" class="val">--</span></div>
            <div class="metric"><span>Daily PnL:</span><span id="dpnl" class="val">--</span></div>
            <div class="metric"><span>DD:</span><span id="dd" class="val">--</span></div>
            <div class="metric"><span>Win Rate:</span><span id="wr" class="val">--</span></div>
        </div>
        <div class="card">
            <h2>Alpha & Microstructure</h2>
            <div class="metric"><span>CVD:</span><span id="cvd" class="val">--</span></div>
            <div class="metric"><span>OB Imbalance:</span><span id="ob" class="val">--</span></div>
            <div class="metric"><span>Funding α:</span><span id="fund" class="val">--</span></div>
            <div class="metric"><span>LiQ Prox:</span><span id="liq" class="val">--</span></div>
        </div>
        <div class="card">
            <h2>Active Trades</h2>
            <div id="trades">Loading...</div>
        </div>
        <div class="card">
            <h2>Activity Log</h2>
            <div id="logs" style="max-height:200px;overflow-y:auto;">Loading...</div>
        </div>
    </div>
    <script>
        const es = new EventSource('/stream');
        es.onmessage = e => {
            const d = JSON.parse(e.data);
            document.getElementById('bal').textContent = `$${d.balance.toFixed(2)}`;
            document.getElementById('dpnl').textContent = `${d.daily_pnl >= 0 ? '+' : ''}${d.daily_pnl.toFixed(2)}`;
            document.getElementById('dpnl').className = 'val ' + (d.daily_pnl >= 0 ? 'pos' : 'neg');
            document.getElementById('dd').textContent = `${((d.peak_bal - d.balance) / d.peak_bal * 100 || 0).toFixed(2)}%`;
            document.getElementById('wr').textContent = `${d.win_rate}%`;
            document.getElementById('cvd').textContent = d.alpha?.cvd?.toFixed(2) || '--';
            document.getElementById('ob').textContent = d.alpha?.ob_imbalance?.toFixed(3) || '--';
            document.getElementById('fund').textContent = (d.alpha?.funding_alpha_bps?.toFixed(2) || '--') + ' bps';
            document.getElementById('liq').textContent = d.alpha?.liq_proximity?.toFixed(2) || '--';

            let tHTML = '';
            d.trades.forEach(t => {
                tHTML += `<div class="trade-row"><span>${t.symbol} ${t.direction}</span> <span class="val ${t.pnl_pos ? 'pos' : 'neg'}">${t.pnl} (${t.pnl_pct})</span></div>`;
            });
            document.getElementById('trades').innerHTML = tHTML || '— no positions —';

            let lHTML = '';
            d.logs.slice(-20).forEach(l => {
                lHTML += `<div class="log-row"><span>[${l.ts}]</span><span>${l.msg}</span></div>`;
            });
            document.getElementById('logs').innerHTML = lHTML || '— waiting —';
        };
    </script>
</body>
</html>"""


# =============================================================================
# FLASK APP FACTORY
# =============================================================================
def _make_app(token: str) -> Flask:
    """Create Flask app with authentication and SSE endpoints."""
    app = Flask(__name__)
    app.secret_key = token + "_secret"

    def _auth(req) -> bool:
        return req.args.get("token") == token or req.cookies.get("bot_token") == token

    def _unauth() -> Response:
        return make_response(
            '<h1>Access token required</h1><form action="/" method="get"><input name="token"><button>Enter</button></form>',
            401,
            {"Content-Type": "text/html"},
        )

    @app.route("/")
    def index() -> Response:
        if not _auth(request):
            return _unauth()
        resp = make_response(_HTML)
        resp.set_cookie("bot_token", token, max_age=86400 * 30, httponly=True, samesite="Lax")
        return resp

    @app.route("/stream")
    def stream() -> Response:
        if not _auth(request):
            return Response("Unauthorized", status=401)

        def event_stream():
            q = queue.Queue(maxsize=50)
            with _sse_lock:
                _sse_queues.append(q)
            try:
                with _state_lock:
                    payload = json.dumps(_state)
                yield f"data: {payload}\n\n"
                while True:
                    try:
                        yield q.get(timeout=30)
                    except queue.Empty:
                        yield ": heartbeat\n\n"
                    except GeneratorExit:
                        break
            finally:
                with _sse_lock:
                    if q in _sse_queues:
                        _sse_queues.remove(q)

        return Response(
            event_stream(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-store",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )

    @app.route("/api/state")
    def api_state() -> Response:
        if not _auth(request):
            return Response('{"error":"unauthorized"}', status=401, mimetype="application/json")
        with _state_lock:
            return Response(json.dumps(_state), mimetype="application/json")

    @app.route("/api/command", methods=["POST"])
    def api_command() -> Response:
        if not _auth(request):
            return Response('{"ok":false,"msg":"unauthorized"}', status=401, mimetype="application/json")
        data = request.get_json(silent=True) or {}
        cmd = data.get("cmd", "")
        engine = _engine_ref
        if engine is None:
            return Response(json.dumps({"ok": False, "msg": "Engine not available"}), mimetype="application/json")

        import asyncio

        loop = getattr(engine, "_loop", None)
        if loop is None or not loop.is_running():
            return Response(json.dumps({"ok": False, "msg": "Loop not running"}), mimetype="application/json")

        cmd_map = {
            "close_all": getattr(engine, "cmd_close_all", None),
            "pause": getattr(engine, "cmd_pause", None),
            "resume": getattr(engine, "cmd_pause", None),
            "stop": getattr(engine, "cmd_stop", None),
        }
        fn = cmd_map.get(cmd)
        if fn:
            asyncio.run_coroutine_threadsafe(fn(), loop)
            return Response(json.dumps({"ok": True, "msg": f"Command '{cmd}' sent"}), mimetype="application/json")
        return Response(json.dumps({"ok": False, "msg": f"Unknown command: {cmd}"}), mimetype="application/json")

    return app


# =============================================================================
# SERVER STARTER
# =============================================================================
def start(port: int = 8080, token: str = "cl_bot") -> None:
    """Start the Flask web dashboard server in a background thread."""
    global _server_thread, _token, _port
    _token = token
    _port = port

    # Suppress Werkzeug logs
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)

    # Prevent WERKZEUG_SERVER_FD issues on Windows
    import os

    os.environ["WERKZEUG_RUN_MAIN"] = "true"

    app = _make_app(token)

    def _run() -> None:
        os.environ.pop("WERKZEUG_SERVER_FD", None)
        os.environ.pop("WERKZEUG_RUN_MAIN", None)
        app.run(host="0.0.0.0", port=port, threaded=True, use_reloader=False)

    _server_thread = threading.Thread(target=_run, daemon=True, name="WebMonitor")
    _server_thread.start()
    logger.info(f"🌐 Web dashboard: http://localhost:{port}/?token={token}")
    print(f"\n  🌐  Dashboard: http://localhost:{port}/?token={token}\n")