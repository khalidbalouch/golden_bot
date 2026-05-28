from __future__ import annotations
import asyncio
import logging
from typing import Dict, Optional, Any
from rich.console import Console
from rich.prompt import Prompt, Confirm

logger = logging.getLogger("golden_bot.ops_console")

class OpsConsole:
    """Human-in-the-loop operator console for intervention."""
    def __init__(self, engine: Optional[Any] = None):
        self.engine = engine
        self.console = Console()
        self._running = False

    async def start_interactive(self) -> None:
        self._running = True
        self.console.print("[bold green]🟢 Golden Bot Ops Console Active[/bold green]")
        while self._running:
            try:
                cmd = Prompt.ask("ops>", default="help")
                await self._handle_cmd(cmd)
            except KeyboardInterrupt:
                self._running = False
            except Exception as e:
                logger.error(f"Ops error: {e}")

    async def _handle_cmd(self, cmd: str) -> None:
        parts = cmd.lower().split()
        if not parts: return
        action = parts[0]

        if action == "close_all":
            if Confirm.ask("⚠️ Close all positions immediately?", default=False):
                await self._exec("close_all")
        elif action == "pause":
            await self._exec("pause")
            self.console.print("[yellow]⏸ Bot paused[/yellow]")
        elif action == "resume":
            await self._exec("resume")
            self.console.print("[green]▶ Bot resumed[/green]")
        elif action == "kill":
            if Confirm.ask("🔴 STOP BOT AND FLATTEN?", default=False):
                await self._exec("close_all")
                await self._exec("stop")
                self._running = False
        elif action == "help":
            self.console.print("Commands: [bold]close_all, pause, resume, kill, exit[/bold]")
        elif action == "exit":
            self._running = False

    async def _exec(self, cmd: str) -> None:
        if self.engine and hasattr(self.engine, f"cmd_{cmd}"):
            fn = getattr(self.engine, f"cmd_{cmd}")
            await fn()
        else:
            self.console.print(f"[red]⚠️ Command '{cmd}' not available on engine[/red]")

    async def stop(self) -> None:
        self._running = False
