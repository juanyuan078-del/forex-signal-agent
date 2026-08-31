# signal_engine.py
# Menggabungkan bias multi-timeframe + indikator entry (RSI, MACD cross,
# Bollinger Bands, VWAP) buat nentuin sinyal BUY/SELL final, lengkap
# dengan level Entry, Stop Loss, dan Take Profit.
#
# CATATAN: Ini murni perhitungan teknikal otomatis, BUKAN nasihat
# keuangan. Pasar forex punya risiko tinggi, selalu verifikasi manual.

from config import FOREX_PAIRS, TIMEFRAME_WEIGHTS, INDICATOR_PARAMS, SIGNAL_THRESHOLD, RISK_REWARD_FX
from mtf_analysis import analyze_pair_mtf, fetch_timeframe_data
from indicators import calc_rsi, calc_macd, calc_bollinger_bands, calc_vwap, calc_atr, calc_ema_cross_signal


def evaluate_entry_trigger(data, params) -> dict:
    """
    Cek kondisi entry di timeframe rendah (H1): apakah ada konfirmasi
    dari RSI, MACD cross, posisi terhadap Bollinger Bands & VWAP.
    """
    close = data["Close"]
    high = data["High"]
    low = data["Low"]
    volume = data["Volume"]

    rsi = calc_rsi(close, params["rsi_period"])
    macd = calc_macd(close, params["macd_fast"], params["macd_slow"], params["macd_signal"])
    bb = calc_bollinger_bands(close, params["bb_period"], params["bb_std"])
    vwap = calc_vwap(high, low, close, volume)
    ema_cross = calc_ema_cross_signal(close, params["ema_fast"], params["ema_slow"])

    harga_sekarang = float(close.iloc[-1])
    rsi_now = float(rsi.iloc[-1]) if len(rsi.dropna()) else None
    macd_hist_now = float(macd["histogram"].iloc[-1]) if len(macd["histogram"].dropna()) else None
    bb_upper = float(bb["upper"].iloc[-1])
    bb_lower = float(bb["lower"].iloc[-1])
    vwap_now = float(vwap.iloc[-1])

    return {
        "harga": harga_sekarang,
        "rsi": round(rsi_now, 1) if rsi_now else None,
        "macd_histogram": round(macd_hist_now, 5) if macd_hist_now else None,
        "bb_upper": round(bb_upper, 5),
        "bb_lower": round(bb_lower, 5),
        "vwap": round(vwap_now, 5),
        "ema_cross": ema_cross,
        "posisi_vs_vwap": "di atas VWAP" if harga_sekarang > vwap_now else "di bawah VWAP",
        "posisi_vs_bb": (
            "dekat BB atas" if harga_sekarang >= bb_upper * 0.998 else
            "dekat BB bawah" if harga_sekarang <= bb_lower * 1.002 else
            "tengah band"
        ),
    }


def calc_fx_levels(entry: float, atr: float, direction: str, rr_config: dict) -> dict:
    """Hitung SL & TP berbasis ATR (Average True Range)."""
    sl_distance = atr * rr_config["sl_atr_multiplier"]

    if direction == "BUY":
        stop_loss = entry - sl_distance
        tp1 = entry + sl_distance * rr_config["tp1_rr"]
        tp2 = entry + sl_distance * rr_config["tp2_rr"]
        tp3 = entry + sl_distance * rr_config["tp3_rr"]
    else:  # SELL
        stop_loss = entry + sl_distance
        tp1 = entry - sl_distance * rr_config["tp1_rr"]
        tp2 = entry - sl_distance * rr_config["tp2_rr"]
        tp3 = entry - sl_distance * rr_config["tp3_rr"]

    return {
        "entry": round(entry, 5),
        "stop_loss": round(stop_loss, 5),
        "tp1": round(tp1, 5),
        "tp2": round(tp2, 5),
        "tp3": round(tp3, 5),
    }


def generate_signal_for_pair(pair_name: str, yf_code: str) -> dict:
    """
    Analisa satu pair penuh: bias MTF + entry trigger, keluarin sinyal
    kalau semua kondisi searah (confluence).
    """
    mtf = analyze_pair_mtf(yf_code, TIMEFRAME_WEIGHTS)
    overall_bias = mtf["overall_bias"]

    h1_data = fetch_timeframe_data(yf_code, "H1")
    if h1_data.empty or len(h1_data) < 30:
        return None

    entry_info = evaluate_entry_trigger(h1_data, INDICATOR_PARAMS)
    atr = calc_atr(h1_data["High"], h1_data["Low"], h1_data["Close"], RISK_REWARD_FX["atr_period"])
    atr_now = float(atr.iloc[-1]) if len(atr.dropna()) else None

    if atr_now is None or entry_info["rsi"] is None:
        return None

    direction = None
    alasan = []

    if overall_bias >= SIGNAL_THRESHOLD["bias_minimum"]:
        if entry_info["rsi"] <= SIGNAL_THRESHOLD["rsi_oversold"] + 15:
            if entry_info["ema_cross"] in ("bullish_cross", "bullish"):
                direction = "BUY"
                alasan.append(f"Bias MTF bullish ({overall_bias})")
                alasan.append(f"RSI H1 {entry_info['rsi']} (area entry)")
                alasan.append(f"EMA cross: {entry_info['ema_cross']}")
                if entry_info["posisi_vs_vwap"] == "di atas VWAP":
                    alasan.append("Harga di atas VWAP (momentum beli)")

    elif overall_bias <= -SIGNAL_THRESHOLD["bias_minimum"]:
        if entry_info["rsi"] >= SIGNAL_THRESHOLD["rsi_overbought"] - 15:
            if entry_info["ema_cross"] in ("bearish_cross", "bearish"):
                direction = "SELL"
                alasan.append(f"Bias MTF bearish ({overall_bias})")
                alasan.append(f"RSI H1 {entry_info['rsi']} (area entry)")
                alasan.append(f"EMA cross: {entry_info['ema_cross']}")
                if entry_info["posisi_vs_vwap"] == "di bawah VWAP":
                    alasan.append("Harga di bawah VWAP (momentum jual)")

    if direction is None:
        return None

    levels = calc_fx_levels(entry_info["harga"], atr_now, direction, RISK_REWARD_FX)

    return {
        "pair": pair_name,
        "direction": direction,
        "overall_bias": overall_bias,
        "mtf_breakdown": mtf["per_timeframe"],
        "entry_info": entry_info,
        "levels": levels,
        "alasan": alasan,
    }


def run_forex_screening() -> list[dict]:
    hasil = []
    for pair_name, yf_code in FOREX_PAIRS.items():
        try:
            signal = generate_signal_for_pair(pair_name, yf_code)
            if signal:
                hasil.append(signal)
        except Exception as e:
            print(f"[ERROR] Gagal analisa {pair_name}: {e}")
            continue
    return hasil
