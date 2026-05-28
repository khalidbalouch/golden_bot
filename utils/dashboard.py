"""
utils/dashboard.py — Professional Rich terminal dashboard
"""
import asyncio
import time
import threading
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich import box

console = Console()


class Dashboard:
    """Rich terminal dashboard for Golden Bot with live updates."""

    def __init__(self, engine=None, config=None):
        self.engine = engine
        self.config = config
        self._live: Optional[Live] = None
        self._running = False
        self._balance = 0.0
        self._peak = 0.0
        self._daily_pnl = 0.0

    def update_balance(self, bal: float):
        """Update balance and track peak."""
        self._balance = bal
        self._peak = max(self._peak, bal)

    def update_daily_pnl(self, pnl: float):
        """Update daily PnL."""
        self._daily_pnl = pnl

    def _format_price(self, p) -> str:
        """Safely format price for display."""
        try:
            # Handle list of prices (take last value)
            if isinstance(p, list) and p:
                p = p[-1]
            p_float = float(p)
            if p_float < 1:
                return f"{p_float:.6f}"
            if p_float < 100:
                return f"{p_float:.4f}"
            return f"{p_float:,.2f}"
        except (ValueError, TypeError):
            return "N/A"

    def _build_display(self):
        """Build the complete Rich dashboard layout."""
        eng = self.engine
        cfg = self.config
        now = time.strftime("%H:%M:%S")
        uptime = int((time.time() - getattr(eng, "_start_time", time.time())) / 60) if eng else 0

        # Get config values safely
        env = getattr(cfg, "env", "?") if cfg else "?"
        market = getattr(cfg, "market", "?") if cfg else "?"
        dry = getattr(cfg, "dry_run", True) if cfg else True
        offline = getattr(eng, "_offline", False) if eng else False
        paused = getattr(eng, "_paused", False) if eng else False
        use_ml = getattr(cfg, "use_ml", False) if cfg else False
        key_file = getattr(cfg, "_key_file", " ") if cfg else " "

        # Build mode string with status indicators
        env_color = "red" if env == "LIVE" else "yellow"
        mode_str = f"[{env_color}]{env}[/{env_color}] | [cyan]{market}[/cyan] "
        if dry:
            mode_str += " | [purple]DRY RUN[/purple] "
        if use_ml:
            mode_str += " | [orange1]ML ON[/orange1] "
        if offline:
            mode_str += " | [yellow]OFFLINE SIM[/yellow] "
        if paused:
            mode_str += " | [bold yellow blink]⏸ PAUSED[/bold yellow blink] "

        # Header panel
        header = Panel(
            Align.center(
                f"[bold cyan]GOLDEN BOT[/bold cyan] {mode_str} [dim]key:{key_file}[/dim] [dim]{now}[/dim] [dim]up[/dim][cyan]{uptime}m[/cyan] "
            ),
            style="cyan",
            box=box.HEAVY,
            height=3
        )

        # Get balance from engine if dashboard not updated yet
        if self._balance == 0.0 and self.engine and getattr(self.engine, "equity", 0) > 0:
            self._balance = self.engine.equity
            self._peak = max(self._peak, self._balance)

        bal = self._balance
        peak = self._peak
        dpnl = self._daily_pnl
        dd = ((peak - bal) / peak * 100) if peak > 0 else 0.0

        # Get metrics from engine
        scans = getattr(eng, "_scan_count", 0) if eng else 0
        sigs = getattr(eng, "_signal_count", 0) if eng else 0
        active_count = len(getattr(eng, "active_trades", {})) if eng else 0

        closed = getattr(eng, "closed_trades", []) if eng else []
        wins = sum(1 for t in closed if getattr(t, "realized_pnl", 0) > 0)
        losses_count = len(closed) - wins
        wr = (wins / len(closed) * 100) if closed else 0.0

        session_start = getattr(eng, "session_start", bal) if eng else bal
        sess_loss = session_start - bal

        # Color coding for metrics
        bal_color = "green" if bal >= peak * 0.97 else "yellow" if bal >= peak * 0.90 else "red"
        dpnl_color = "green" if dpnl >= 0 else "red"
        sl_color = "red" if sess_loss > 0 else "green"

        # ── Account Table ─────────────────────────────────────────────────
        acct_table = Table(show_header=False, box=box.SIMPLE, border_style="dim cyan", padding=(0, 1))
        acct_table.add_column(" ", style="dim", width=18)
        acct_table.add_column(" ", width=18)
        acct_table.add_column(" ", style="dim", width=18)
        acct_table.add_column(" ", width=18)
        acct_table.add_column(" ", style="dim", width=18)
        acct_table.add_column(" ", width=16)

        open_pnl = getattr(eng, "open_pnl", 0) if eng else 0
        acct_table.add_row(
            "Wallet ", f"[{bal_color}]${self._format_price(bal)}[/{bal_color}] ",
            "Open PnL ", f"[{'green' if open_pnl >= 0 else 'red'}]{open_pnl:+.4f}[/] ",
            "Daily PnL ", f"[{dpnl_color}]{dpnl:+.4f}[/{dpnl_color}] ",
        )
        acct_table.add_row(
            "Peak ", f"[cyan]${self._format_price(peak)}[/cyan] ",
            "Drawdown ", f"[{'red' if dd > 5 else 'yellow' if dd > 2 else 'green'}]{dd:.2f}%[/] ",
            "Session Loss ", f"[{sl_color}]{sess_loss:+.4f}[/{sl_color}] ",
        )
        acct_table.add_row(
            "Scans ", f"[cyan]{scans}[/cyan] ",
            "Signals ", f"[cyan]{sigs}[/cyan] ",
            "W/L/WR ", f"[green]{wins}[/green]/[red]{losses_count}[/red] [dim]{wr:.1f}%[/dim] ",
        )
        acct_table.add_row(
            "Active ", f"[cyan]{active_count}[/cyan] ",
            "Score Gate ", f"[yellow]{getattr(cfg, 'score_gate', 45)}%[/yellow] ",
            "Lev ", f"[purple]{getattr(cfg, 'leverage', 1)}x[/purple] ",
        )

        acct_panel = Panel(acct_table, title="[bold cyan]▸ ACCOUNT[/bold cyan] ", style="cyan", box=box.HEAVY_HEAD)

        # ── Active Trades ─────────────────────────────────────────────────
        trade_table = Table(
            show_header=True, box=box.SIMPLE_HEAD, border_style="dim cyan", header_style="bold dim cyan"
        )
        trade_table.add_column("ID ", style="dim", width=8)
        trade_table.add_column("Symbol ", width=10)
        trade_table.add_column("Dir ", width=8)
        trade_table.add_column("Entry ", width=12)
        trade_table.add_column("Current ", width=12)
        trade_table.add_column("PnL $ ", width=12)
        trade_table.add_column("PnL % ", width=9)
        trade_table.add_column("SL ", style="red", width=12)
        trade_table.add_column("TP1 ", style="green", width=12)
        trade_table.add_column("Score ", style="yellow", width=7)
        trade_table.add_column("Flags ", width=10)
        trade_table.add_column("Age ", style="dim", width=6)

        active_trades = dict(getattr(eng, "active_trades", {})) if eng else {}
        prices = dict(getattr(eng, "prices", {})) if eng else {}

        if not active_trades:
            for _ in range(3):
                trade_table.add_row(*["— "] * 12)
        else:
            for t in list(active_trades.values())[:3]:
                # ✅ FIX: Get current price safely from list
                price_val = prices.get(t.symbol, [t.entry_price])
                cp = price_val[-1] if isinstance(price_val, list) and price_val else price_val

                try:
                    cp_float = float(cp)
                except (ValueError, TypeError):
                    cp_float = t.entry_price  # Fallback to entry price

                upnl = t.unrealized_pnl(cp_float) if hasattr(t, "unrealized_pnl") else 0
                ppct = t.pnl_pct(cp_float) if hasattr(t, "pnl_pct") else 0
                age = int((time.time() - getattr(t, "open_time", time.time())) / 60)
                pnl_color = "green" if upnl >= 0 else "red"

                # Handle direction (enum or string)
                direction = getattr(t, "direction", "")
                if hasattr(direction, "value"):
                    direction = direction.value
                dir_color = "green" if str(direction).upper() == "LONG" else "red"

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

                trade_table.add_row(
                    t.trade_id,
                    f"[bold]{t.symbol}[/bold] ",
                    f"[{dir_color}]{str(direction).upper()}[/{dir_color}] ",
                    self._format_price(t.entry_price),
                    f"[cyan]{self._format_price(cp_float)}[/cyan] ",
                    f"[{pnl_color}]{upnl:+.4f}[/{pnl_color}] ",
                    f"[{pnl_color}]{ppct:+.2f}%[/{pnl_color}] ",
                    self._format_price(t.sl_price),
                    self._format_price(t.tp1_price),
                    f"{getattr(t, 'score', 0):.1f} ",
                    f"[cyan]{flags.strip() or '·'}[/cyan] ",
                    f"{age}m ",
                )

        trade_panel = Panel(
            trade_table,
            title=f"[bold cyan]▸ ACTIVE TRADES[/bold cyan] [dim]({active_count} open)[/dim] ",
            style="cyan",
            box=box.HEAVY_HEAD,
        )

        # ── Market Regimes ───────────────────────────────────────────────
        regimes = dict(getattr(eng, "regimes", {})) if eng else {}
        regime_lines = []
        for sym, regime in list(regimes.items())[:3]:
            # ✅ FIX: Get last price from list, not the list itself
            price_list = prices.get(sym, [0])
            cp = price_list[-1] if isinstance(price_list, list) and price_list else price_list

            r_val = str(regime)
            if hasattr(regime, "value"):
                r_val = regime.value
            r_color = "green" if r_val == "UPTREND" else "red" if r_val == "DOWNTREND" else "yellow"

            # ✅ FIX: Ensure cp is a float before formatting
            try:
                cp_float = float(cp)
                regime_lines.append(
                    f"  [bold]{sym:12s}[/bold] [dim]${cp_float:,.4f}[/dim]  [{r_color}]{r_val}[/{r_color}] "
                )
            except (ValueError, TypeError):
                regime_lines.append(
                    f"  [bold]{sym:12s}[/bold] [dim]$N/A[/dim]  [{r_color}]{r_val}[/{r_color}] "
                )

        regime_panel = Panel(
            "\n".join(regime_lines) if regime_lines else "[dim]  — scanning —[/dim] ",
            title="[bold cyan]▸ MARKET REGIMES[/bold cyan] ",
            style="cyan",
            box=box.HEAVY_HEAD,
        )

        # ── Activity Log ─────────────────────────────────────────────────
        logs = []
        if self.engine and hasattr(self.engine, "web_monitor") and self.engine.web_monitor:
            wm_state = getattr(self.engine.web_monitor, "_state", {})
            raw_logs = wm_state.get("logs", [])[-10:] if wm_state else []
            for entry in raw_logs:
                if isinstance(entry, dict):
                    logs.append(f"[dim]{entry.get('ts', ''): <8}[/dim] {entry.get('msg', '')} ")
                else:
                    logs.append(str(entry))

        if not logs:
            logs = ["[dim]  — waiting for activity —[/dim] "]

        log_panel = Panel(
            "\n".join(logs),
            title="[bold cyan]▸ ACTIVITY LOG[/bold cyan] ",
            style="cyan",
            box=box.HEAVY_HEAD,
        )

        # ── Controls Hint ────────────────────────────────────────────────
        ctrl_text = (
            f"[dim]  Web Dashboard: [cyan]http://localhost:{getattr(self, '_port', 8080)}/?token={getattr(self, '_token', 'cl_bot')}[/cyan]  │   "
            "[ESC/Ctrl+C] Stop[/dim] "
        )
        ctrl_panel = Panel(Align.center(ctrl_text), style="dim", box=box.SIMPLE, height=3)

        # ── Layout Assembly ──────────────────────────────────────────────
        from rich.columns import Columns

        layout = Table.grid(expand=True)
        layout.add_column()
        layout.add_row(header)
        layout.add_row(acct_panel)
        layout.add_row(trade_panel)
        layout.add_row(Columns([regime_panel], expand=True))
        layout.add_row(log_panel)
        layout.add_row(ctrl_panel)

        return layout

    async def start(self):
        """Start the live Rich dashboard."""
        self._running = True
        with Live(self._build_display(), refresh_per_second=2, screen=False) as live:
            self._live = live
            while self._running:
                live.update(self._build_display())
                await asyncio.sleep(0.5)

    def stop(self):
        """Stop the dashboard."""
        self._running = False