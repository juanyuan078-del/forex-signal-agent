# mtf_analysis.py
# Ambil data harga per timeframe (Weekly, Daily, H4, H1, M15) dan
# hitung "bias" (kecenderungan arah) tiap timeframe berdasarkan
# EMA trend, RSI momentum, dan MACD histogram.

import yfinance as yf
import pandas as pd
from config import INDICATOR_PARAMS
from indicators import calc_rsi, calc_ema, calc_macd


def fetch_timeframe_data(yf_code: str, timeframe: str) -> pd.DataFrame:
    """
    Ambil data harga sesuai timeframe. yfinance gak punya interval native
    buat H4/Weekly-resample-dari-intraday, jadi kita resample manual dari
    data dasar yang paling deket.
    """
    if timeframe == "W":
        data = yf.Ticker(yf_code).history(period="2y", interval="1wk")
    elif timeframe == "D":
        data = yf.Ticker(yf_code).history(period="1y", interval="1d")
    elif timeframe == "H4":
        # Resample dari data H1 (60 hari terakhir, batas maksimal yfinance buat interval 1h)
        h1 = yf.Ticker(yf_code).history(period="60d", interval="1h")
        data = resample_ohlc(h1, "4h")
    elif timeframe == "H1":
        data = yf.Ticker(yf_code).history(period="30d", interval="1h")
    elif timeframe == "M15":
        data = yf.Ticker(yf_code).history(period="5d", interval="15m")
    else:
        raise ValueError(f"Timeframe gak dikenali: {timeframe}")

    return data


def resample_ohlc(data: pd.DataFrame, rule: str) -> pd.DataFrame:
    if data.empty:
        return data
    return data.resample(rule).agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum",
    }).dropna()


def calc_timeframe_bias(data: pd.DataFrame) -> dict:
    """
    Hitung skor bias untuk satu timeframe: -1 (bearish kuat) sampai +1 (bullish kuat).
    Kombinasi dari: posisi harga vs EMA50, RSI vs 50, dan MACD histogram.
    """
    if data.empty or len(data) < INDICATOR_PARAMS["ema_slow"] + 2:
        return {"score": 0, "label": "data kurang", "rsi": None}

    close = data["Close"]
    ema_fast = calc_ema(close, INDICATOR_PARAMS["ema_fast"])
    ema_slow = calc_ema(close, INDICATOR_PARAMS["ema_slow"])
    rsi = calc_rsi(close, INDICATOR_PARAMS["rsi_period"])
    macd = calc_macd(
        close,
        INDICATOR_PARAMS["macd_fast"],
        INDICATOR_PARAMS["macd_slow"],
        INDICATOR_PARAMS["macd_signal"],
    )

    score = 0
    # Komponen 1: posisi EMA fast vs slow (trend)
    if ema_fast.iloc[-1] > ema_slow.iloc[-1]:
        score += 1
    else:
        score -= 1

    # Komponen 2: RSI di atas/bawah 50 (momentum)
    rsi_now = rsi.iloc[-1]
    if pd.notna(rsi_now):
        if rsi_now > 50:
            score += 1
        else:
            score -= 1

    # Komponen 3: MACD histogram positif/negatif (konfirmasi momentum)
    hist_now = macd["histogram"].iloc[-1]
    if pd.notna(hist_now):
        if hist_now > 0:
            score += 1
        else:
            score -= 1

    normalized_score = score / 3  # jadi rentang -1 s/d 1

    if normalized_score >= 0.5:
        label = "BULLISH"
    elif normalized_score <= -0.5:
        label = "BEARISH"
    else:
        label = "NETRAL"

    return {
        "score": round(normalized_score, 2),
        "label": label,
        "rsi": round(rsi_now, 1) if pd.notna(rsi_now) else None,
    }


def analyze_pair_mtf(yf_code: str, weights: dict) -> dict:
    """
    Analisa satu pair di semua timeframe, hitung bias gabungan (weighted).
    """
    results = {}
    weighted_total = 0

    for tf, weight in weights.items():
        data = fetch_timeframe_data(yf_code, tf)
        bias = calc_timeframe_bias(data)
        results[tf] = bias
        weighted_total += bias["score"] * weight

    return {
        "per_timeframe": results,
        "overall_bias": round(weighted_total, 2),
    }
