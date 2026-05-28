"""
core/features.py — Feature engineering for ML signal generation
"""
import pandas as pd
import numpy as np

# Try to import TA-Lib, fallback to pandas calculations
try:
    import talib

    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False
    print("⚠️ TA-Lib not found — using pandas fallback for indicators")


def generate_features(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Generate technical, microstructure, and regime features for ML training.

    Args:
        df: DataFrame with OHLCV data (index: timestamp)
        symbol: Trading pair (for symbol-specific features)

    Returns:
        DataFrame with added feature columns + target variables
    """
    df = df.copy()

    # === Technical Indicators ===
    if HAS_TALIB:
        # Trend
        df["sma_20"] = talib.SMA(df["close"], timeperiod=20)
        df["sma_50"] = talib.SMA(df["close"], timeperiod=50)
        df["ema_12"] = talib.EMA(df["close"], timeperiod=12)
        df["ema_26"] = talib.EMA(df["close"], timeperiod=26)
        df["macd"], df["macd_signal"], df["macd_hist"] = talib.MACD(df["close"])

        # Momentum
        df["rsi_14"] = talib.RSI(df["close"], timeperiod=14)
        df["stoch_k"], df["stoch_d"] = talib.STOCH(df["high"], df["low"], df["close"])
        df["cci_20"] = talib.CCI(df["high"], df["low"], df["close"], timeperiod=20)

        # Volatility
        df["atr_14"] = talib.ATR(df["high"], df["low"], df["close"], timeperiod=14)
        df["bb_upper"], df["bb_middle"], df["bb_lower"] = talib.BBANDS(df["close"])

        # Volume
        df["obv"] = talib.OBV(df["close"], df["volume"])
    else:
        # Pandas fallback calculations
        df["sma_20"] = df["close"].rolling(20).mean()
        df["sma_50"] = df["close"].rolling(50).mean()
        df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
        df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()
        df["macd"] = df["ema_12"] - df["ema_26"]
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # RSI fallback
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi_14"] = 100 - (100 / (1 + rs))

        # Bollinger Bands fallback
        rolling_std = df["close"].rolling(20).std()
        df["bb_middle"] = df["close"].rolling(20).mean()
        df["bb_upper"] = df["bb_middle"] + (rolling_std * 2)
        df["bb_lower"] = df["bb_middle"] - (rolling_std * 2)

    # === Derived Features ===
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
    df["price_vs_sma20"] = df["close"] / df["sma_20"] - 1
    df["price_vs_sma50"] = df["close"] / df["sma_50"] - 1
    df["volatility_20"] = df["close"].rolling(20).std() / df["close"]

    # === Microstructure Features (Futures-specific) ===
    # These require additional API calls — placeholders for now
    df["funding_rate"] = 0.0  # Fetch from /fapi/v1/premiumIndex in production
    df["oi_change"] = df["volume"].pct_change()  # Placeholder for open interest

    # === Target Variables for Supervised Learning ===
    # Next 15-min return (for 15m timeframe)
    df["target_return_15m"] = df["close"].shift(-15) / df["close"] - 1
    df["target_direction"] = (df["target_return_15m"] > 0).astype(int)

    # Next 1-hour return
    df["target_return_1h"] = df["close"].shift(-60) / df["close"] - 1

    # Classification targets with thresholds
    df["target_up_strong"] = (df["target_return_15m"] > 0.002).astype(int)  # >0.2% move
    df["target_down_strong"] = (df["target_return_15m"] < -0.002).astype(int)

    # Drop rows with NaN targets (from shifting)
    df = df.dropna(subset=["target_return_15m", "target_direction"])

    # Add metadata
    df.attrs["symbol"] = symbol
    df.attrs["feature_count"] = len([c for c in df.columns if c.startswith(("sma", "ema", "rsi", "macd", "target"))])

    return df