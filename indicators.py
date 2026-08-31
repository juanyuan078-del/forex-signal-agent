# indicators.py
# Kumpulan fungsi hitung indikator teknikal: RSI, MACD, Bollinger Bands,
# EMA, VWAP, ATR. Dipakai buat analisa tiap timeframe.

import pandas as pd
import numpy as np


def calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))


def calc_ema(close: pd.Series, period: int) -> pd.Series:
    return close.ewm(span=period, adjust=False).mean()


def calc_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    ema_fast = calc_ema(close, fast)
    ema_slow = calc_ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calc_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


def calc_bollinger_bands(close: pd.Series, period: int = 20, std_dev: float = 2) -> dict:
    middle = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    return {"upper": upper, "middle": middle, "lower": lower}


def calc_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    VWAP (Volume Weighted Average Price), dihitung dari awal data yang tersedia
    (anchored VWAP). Forex data dari yfinance kadang volume-nya 0/kosong
    (karena forex OTC), jadi fallback pakai typical price kalau volume gak ada.
    """
    typical_price = (high + low + close) / 3
    if volume.sum() == 0:
        return typical_price.expanding().mean()
    cumulative_vol = volume.cumsum()
    cumulative_vol_price = (typical_price * volume).cumsum()
    return cumulative_vol_price / cumulative_vol.replace(0, 1e-10)


def calc_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def calc_ema_cross_signal(close: pd.Series, fast_period: int, slow_period: int) -> str:
    """
    Deteksi posisi EMA fast vs slow saat ini, dan apakah baru aja cross.
    Return: 'bullish_cross', 'bearish_cross', 'bullish', 'bearish', atau 'neutral'.
    """
    ema_fast = calc_ema(close, fast_period)
    ema_slow = calc_ema(close, slow_period)

    if len(close) < slow_period + 2:
        return "neutral"

    today_above = ema_fast.iloc[-1] > ema_slow.iloc[-1]
    yesterday_above = ema_fast.iloc[-2] > ema_slow.iloc[-2]

    if today_above and not yesterday_above:
        return "bullish_cross"
    elif not today_above and yesterday_above:
        return "bearish_cross"
    elif today_above:
        return "bullish"
    else:
        return "bearish"
