import pytest
import asyncio
from pathlib import Path
from utils.graceful_shutdown import persist_state, load_state

@pytest.mark.asyncio
async def test_state_persistence(tmp_path):
    import utils.graceful_shutdown as gs
    gs._state_file = tmp_path / "state.json"
    await persist_state({"balance": 100.0, "active": 3})
    state = await load_state()
    assert state["balance"] == 100.0
    assert state["active"] == 3
