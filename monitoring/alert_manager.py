from __future__ import annotations
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Any
import httpx

logger = logging.getLogger("golden_bot.monitoring.alerts")

@dataclass
class Alert:
    rule_name: str
    severity: Literal["INFO", "WARNING", "CRITICAL"]
    message: str
    labels: Dict[str, str] = field(default_factory=dict)
    fingerprint: str = ""
    start_time: float = 0.0
    resolved: bool = False

    def __post_init__(self):
        if not self.fingerprint:
            self.fingerprint = f"{self.rule_name}__{json.dumps(self.labels, sort_keys=True)}"
        if self.start_time == 0.0:
            self.start_time = time.time()

@dataclass
class AlertRule:
    name: str
    condition: str
    severity: Literal["INFO", "WARNING", "CRITICAL"]
    threshold: float
    window_sec: int = 300

class AlertManager:
    """Central alert routing, deduplication, and escalation engine."""
    def __init__(self, webhook_url: Optional[str] = None, dedup_window_sec: int = 300):
        self.webhook = webhook_url
        self.dedup_window = dedup_window_sec
        self._active: Dict[str, Alert] = {}
        self._history: List[Alert] = []
        self._rules: List[AlertRule] = [
            AlertRule("high_drawdown", "drawdown_pct > threshold", "CRITICAL", 0.10),
            AlertRule("model_drift", "psi > threshold", "WARNING", 0.20),
            AlertRule("queue_backlog", "queue_depth > threshold", "WARNING", 100),
        ]

    async def evaluate_rules(self, metrics: Dict[str, float]) -> List[Alert]:
        triggered = []
        for rule in self._rules:
            metric_val = metrics.get(rule.condition.split(" > ")[0], 0.0)
            if metric_val > rule.threshold:
                alert = Alert(rule.name, rule.severity, f"{rule.name} exceeded {rule.threshold}", {"metric": rule.condition.split(" > ")[0]})
                if self._is_deduplicated(alert):
                    continue
                triggered.append(alert)
                self._active[alert.fingerprint] = alert
                await self._dispatch(alert)
        return triggered

    def _is_deduplicated(self, alert: Alert) -> bool:
        prev = self._history[-1] if self._history else None
        if prev and prev.fingerprint == alert.fingerprint and (time.time() - prev.start_time) < self.dedup_window:
            return True
        return False

    async def _dispatch(self, alert: Alert) -> None:
        if not self.webhook:
            logger.warning(f"🚨 Alert: {alert.rule_name} [{alert.severity}] {alert.message}")
            return
        payload = {
            "text": f"**[{alert.severity}] {alert.rule_name}**: {alert.message}",
            "labels": alert.labels,
            "timestamp": alert.start_time
        }
        try:
            async with httpx.AsyncClient() as client:
                await client.post(self.webhook, json=payload, timeout=5.0)
        except Exception as e:
            logger.error(f"Alert dispatch failed: {e}")
        self._history.append(alert)
