# config.py
# Konfigurasi pair forex & parameter indikator.
# Silakan tambah pair lain di FOREX_PAIRS sesuai kebutuhan.

# Format kode yfinance buat forex: "EURUSD=X"
FOREX_PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
}

# ==== Bobot tiap timeframe buat hitung bias keseluruhan ====
# Total harus 100. Timeframe lebih tinggi = bobot lebih besar
# (searah tren besar dianggap lebih penting daripada noise jangka pendek).
TIMEFRAME_WEIGHTS = {
    "W": 0.25,   # Weekly
    "D": 0.25,   # Daily
    "H4": 0.25,  # 4 Jam
    "H1": 0.15,  # 1 Jam
    "M15": 0.10, # 15 Menit (buat timing entry)
}

# ==== Parameter indikator ====
INDICATOR_PARAMS = {
    "rsi_period": 14,
    "ema_fast": 20,
    "ema_slow": 50,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_period": 20,
    "bb_std": 2,
}

# ==== Ambang batas buat nentuin sinyal ====
SIGNAL_THRESHOLD = {
    "bias_minimum": 0.5,     # skor bias minimal (dari -1 ke 1) buat dianggap searah tren
    "rsi_oversold": 35,
    "rsi_overbought": 65,
}

# ==== Perhitungan Stop Loss & Take Profit ====
# Berbasis ATR (Average True Range) biar sesuai volatilitas tiap pair,
# bukan persentase tetap kaya di saham (forex butuh presisi pip).
RISK_REWARD_FX = {
    "atr_period": 14,
    "sl_atr_multiplier": 1.5,   # SL = 1.5x ATR dari entry
    "tp1_rr": 1.5,
    "tp2_rr": 2.5,
    "tp3_rr": 4.0,
}
