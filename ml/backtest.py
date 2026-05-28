"""
ml/backtest.py — Vectorized backtesting for strategy validation
"""
import pandas as pd
import numpy as np


def backtest_strategy(df: pd.DataFrame, signal_col: str, transaction_cost: float = 0.0004):
    """
    Simple vectorized backtest.
    df must have: 'close', signal_col (1=BUY, -1=SELL, 0=HOLD)
    """
    df = df.copy()

    # Generate positions: shift signal to avoid lookahead bias
    df['position'] = df[signal_col].shift(1)

    # Calculate returns
    df['market_return'] = df['close'].pct_change()
    df['strategy_return'] = df['position'] * df['market_return']

    # Apply transaction costs on position changes
    df['position_change'] = df['position'].diff().abs()
    df['strategy_return'] -= df['position_change'] * transaction_cost

    # Cumulative returns
    df['cum_market'] = (1 + df['market_return']).cumprod()
    df['cum_strategy'] = (1 + df['strategy_return']).cumprod()

    # Metrics
    total_return = df['cum_strategy'].iloc[-1] - 1
    sharpe = np.sqrt(252 * 4) * df['strategy_return'].mean() / df['strategy_return'].std()  # 15-min data
    max_dd = (df['cum_strategy'].cummax() - df['cum_strategy']).max()

    return {
        'total_return': total_return,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_dd,
        'win_rate': (df[df['position'] != 0]['strategy_return'] > 0).mean(),
        'final_equity': df['cum_strategy'].iloc[-1]
    }