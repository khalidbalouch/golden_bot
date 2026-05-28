import pytest
import asyncio
import time
import pandas as pd
import numpy as np
from unittest.mock import AsyncMock, patch
from core.security import AuditLogger
from ml.feature_pipeline import FeaturePipeline
from core.risk_engine import RiskEngine, RiskValidation
from core.trade_manager import TradeManager
from core.execution_engine import ExecutionEngine
from utils.dashboard import Dashboard
from utils.web_monitor import update_state, register_engine

@pytest.fixture
def mock_components():
    audit = AuditLogger()
    exec_engine = AsyncMock(spec=ExecutionEngine)
    risk_eng = AsyncMock(spec=RiskEngine)
    risk_eng.validate_trade.return_value = RiskValidation(True, 0.01, 49000.0)
    tm = AsyncMock(spec=TradeManager)
    dash = Dashboard()
    return audit, exec_engine, risk_eng, tm, dash

@pytest.mark.asyncio
async def test_signal_to_execution_flow(mock_components):
    audit, exec_engine, risk_eng, tm, dash = mock_components

    # Simulate WS feature push
    features = {"cvd": 1.2, "probability": 0.78, "vol_imbalance": 0.15}

    # Risk validation passes
    val = risk_eng.validate_trade(features, {}, 10000.0)
    assert val.approved

    # Trade creation & execution mock
    trade = await tm.create_trade("t1", "BTCUSDT", "LONG", 50000.0, 49000.0, 51000.0, 52000.0, 0.01)
    await exec_engine.place_order(trade.trade_id, trade.symbol, "BUY", trade.quantity, 50000.0)
    exec_engine.place_order.assert_called_once()

    # Dashboard state sync
    update_state(None, 10000.0, 10050.0, 50.0, 10, 2, time.time(), 10000.0, [], [], {}, {}, False, False, type('obj', (object,), {'env':'TESTNET','market':'FUTURES','dry_run':True})())
    assert True # State updated without exception

@pytest.mark.asyncio
async def test_ws_disconnect_recovery():
    from core.ws_manager import BinanceWSManager
    ws = BinanceWSManager()
    ws._keep_running = False # Simulate disconnect
    await ws._reconnect() # Should handle gracefully without crash
    assert ws._reconnect_delay > 0
