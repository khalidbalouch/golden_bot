from __future__ import annotations
import gymnasium as gym
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from gymnasium import spaces

class CryptoTradingEnv(gym.Env):
    """Gymnasium-compliant environment for RL training."""
    metadata = {"render_modes": ["human"]}

    def __init__(self,  pd.DataFrame, balance: float = 10000.0, 
                 window_size: int = 50, commission: float = 0.0005,
                 reward_fn: str = "sharpe"):
        super().__init__()
        self.df = df.copy()
        self.initial_balance = balance
        self.commission = commission
        self.reward_fn = reward_fn
        self.window_size = window_size

        # State shape: (window_size, num_features)
        self.num_features = len(df.columns) - 1 # exclude timestamp if present
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, 
            shape=(window_size, self.num_features), dtype=np.float32
        )

        # Action space: [0: Hold, 1: Buy, 2: Sell] or continuous [-1:1]
        self.action_space = spaces.Discrete(3) 

        self._reset_state()

    def _reset_state(self) -> None:
        self.balance = self.initial_balance
        self.position = 0.0
        self.entry_price = 0.0
        self.current_step = self.window_size
        self.net_worth_history = [self.initial_balance]
        self._done = False

    def reset(self, seed: Optional[int] = None, options: Optional[dict] = None) -> Tuple[np.ndarray, dict]:
        super().reset(seed=seed)
        self._reset_state()
        obs = self._get_observation()
        info = {"balance": self.balance, "net_worth": self.initial_balance}
        return obs, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, dict]:
        current_price = self.df.iloc[self.current_step]["close"]
        prev_net_worth = self._calculate_net_worth(current_price)

        # Execute action
        if action == 1: # Buy
            if self.position <= 0:
                amount = self.balance / current_price
                self.position += amount * (1 - self.commission)
                self.balance -= amount * current_price
                self.entry_price = current_price
        elif action == 2: # Sell
            if self.position > 0:
                self.balance += self.position * current_price * (1 - self.commission)
                self.position = 0.0
                self.entry_price = 0.0

        self.current_step += 1
        terminated = self.current_step >= len(self.df) - 1
        truncated = False

        reward = self._calculate_reward(prev_net_worth, current_price)
        obs = self._get_observation()
        info = {"balance": self.balance, "position": self.position}

        return obs, reward, terminated, truncated, info

    def _get_observation(self) -> np.ndarray:
        start = self.current_step - self.window_size
        end = self.current_step
        data = self.df.iloc[start:end].values
        return data.astype(np.float32)

    def _calculate_net_worth(self, price: float) -> float:
        return self.balance + (self.position * price)

    def _calculate_reward(self, prev_net_worth: float, price: float) -> float:
        net_worth = self._calculate_net_worth(price)
        returns = (net_worth - prev_net_worth) / prev_net_worth

        if self.reward_fn == "sharpe":
            self.net_worth_history.append(net_worth)
            if len(self.net_worth_history) > 20:
                rews = pd.Series(self.net_worth_history).pct_change().dropna()
                return (rews.mean() / (rews.std() + 1e-9)) * np.sqrt(252)
        return returns
