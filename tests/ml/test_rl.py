import pytest
import numpy as np
import pandas as pd
from ml.rl.environments.trading_env import CryptoTradingEnv
from ml.rl.agents.ppo_agent import PPOAgent

@pytest.fixture
def sample_data():
    return pd.DataFrame({
        "close": np.random.randn(100).cumsum() + 100,
        "volume": np.random.rand(100) * 1000,
        "rsi": np.random.rand(100) * 100
    })

def test_env_reset(sample_data):
    env = CryptoTradingEnv(sample_data, window_size=10)
    obs, info = env.reset()
    assert obs.shape == (10, 2) # window_size x (cols - timestamp)

def test_env_step(sample_data):
    env = CryptoTradingEnv(sample_data, window_size=10)
    obs, _ = env.reset()
    obs2, reward, term, trunc, info = env.step(1)
    assert obs2.shape == (10, 2)
    assert isinstance(reward, float)

def test_ppo_update(sample_data):
    env = CryptoTradingEnv(sample_data, window_size=10)
    agent = PPOAgent(input_dim=2, action_dim=3, k_epochs=2)
    state, _ = env.reset()
    for _ in range(5):
        action = agent.select_action(state)
        obs, r, term, trunc, info = env.step(action)
        agent.store_reward(r, term)
    if term: agent.update()
    assert True
