from __future__ import annotations
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Tuple, Dict
from torch.distributions import Categorical

class ActorCriticNetwork(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, action_dim: int):
        super().__init__()
        self.actor = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, action_dim)
        )
        self.critic = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.actor(x), self.critic(x)

class PPOAgent:
    """Proximal Policy Optimization for discrete trading actions."""
    def __init__(self, input_dim: int, action_dim: int, lr: float = 3e-4, 
                 gamma: float = 0.99, eps_clip: float = 0.2, k_epochs: int = 4):
        self.gamma = gamma
        self.eps_clip = eps_clip
        self.k_epochs = k_epochs
        self.policy = ActorCriticNetwork(input_dim, 128, action_dim)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=lr)
        self.memory_states = []
        self.memory_actions = []
        self.memory_log_probs = []
        self.memory_rewards = []
        self.memory_dones = []

    def select_action(self, state: np.ndarray, deterministic: bool = False) -> int:
        state_tensor = torch.FloatTensor(state.flatten())
        with torch.no_grad():
            action_probs, _ = self.policy(state_tensor)
            dist = Categorical(logits=action_probs)
            if deterministic:
                action = torch.argmax(action_probs).item()
            else:
                action = dist.sample().item()
        log_prob = dist.log_prob(torch.tensor(action))

        self.memory_states.append(state)
        self.memory_actions.append(action)
        self.memory_log_probs.append(log_prob)
        return action

    def store_reward(self, reward: float, done: bool) -> None:
        self.memory_rewards.append(reward)
        self.memory_dones.append(done)

    def update(self) -> Dict[str, float]:
        # Compute returns and advantages
        rewards = []
        discounted_r = 0
        for r, done in zip(reversed(self.memory_rewards), reversed(self.memory_dones)):
            discounted_r = r + self.gamma * discounted_r * (1 - done)
            rewards.insert(0, discounted_r)
        rewards = torch.tensor(rewards, dtype=torch.float32)
        rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-9)

        losses = []
        for _ in range(self.k_epochs):
            states = torch.FloatTensor(self.memory_states)
            actions = torch.LongTensor(self.memory_actions)
            old_log_probs = torch.stack(self.memory_log_probs)

            action_probs, state_values = self.policy(states)
            dist = Categorical(logits=action_probs)
            new_log_probs = dist.log_prob(actions)
            ratios = torch.exp(new_log_probs - old_log_probs)

            advantages = rewards - state_values.squeeze()
            surr1 = ratios * advantages
            surr2 = torch.clamp(ratios, 1-self.eps_clip, 1+self.eps_clip) * advantages
            actor_loss = -torch.min(surr1, surr2).mean()
            critic_loss = nn.MSELoss()(state_values.squeeze(), rewards)
            entropy = dist.entropy().mean()

            loss = actor_loss + 0.5 * critic_loss - 0.01 * entropy
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            losses.append(loss.item())

        self.memory_states.clear()
        self.memory_actions.clear()
        self.memory_log_probs.clear()
        self.memory_rewards.clear()
        self.memory_dones.clear()
        return {"actor_loss": losses[-1] if losses else 0}
