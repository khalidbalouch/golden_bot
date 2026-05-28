#!/usr/bin/env python3
"""CLI: Train RL agent using PPO on historical data"""
import argparse
import logging
import sys
import pandas as pd
sys.path.insert(0, ".")
from ml.rl.environments.trading_env import CryptoTradingEnv
from ml.rl.agents.ppo_agent import PPOAgent

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("train_rl")

def main(data_path: str, epochs: int = 100):
    logger.info(f"🤖 Training PPO Agent on {data_path}")
    df = pd.read_csv(data_path)
    env = CryptoTradingEnv(df, balance=10000.0)
    agent = PPOAgent(input_dim=env.num_features, action_dim=3)

    for ep in range(epochs):
        state, _ = env.reset()
        done = False
        while not done:
            action = agent.select_action(state)
            next_state, reward, terminated, truncated, info = env.step(action)
            agent.store_reward(reward, terminated)
            if terminated:
                agent.update()
            done = terminated or truncated
        if ep % 10 == 0:
            logger.info(f"Episode {ep} | Net Worth: {info['net_worth']:.2f}")
    logger.info("✅ RL Training complete. Saving model...")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--epochs", type=int, default=100)
    args = p.parse_args()
    main(args.data, args.epochs)
