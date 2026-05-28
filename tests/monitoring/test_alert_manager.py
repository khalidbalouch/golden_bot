import pytest
import asyncio
from monitoring.alert_manager import AlertManager, AlertRule

@pytest.mark.asyncio
async def test_rule_evaluation():
manager = AlertManager(dedup_window_sec=100)
manager._rules = [AlertRule("test_rule", "metric > threshold", "WARNING", 0.5)]

alerts = await manager.evaluate_rules({"metric": 0.8})
assert len(alerts) == 1
assert alerts[0].rule_name == "test_rule"

@pytest.mark.asyncio
async def test_deduplication():
manager = AlertManager(dedup_window_sec=100)
manager._rules = [AlertRule("test_rule", "metric > threshold", "WARNING", 0.5)]

await manager.evaluate_rules({"metric": 0.9})
alerts2 = await manager.evaluate_rules({"metric": 0.95})
assert len(alerts2) == 0
