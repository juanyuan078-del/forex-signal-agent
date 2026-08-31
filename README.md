# Forex Signal Agent

Analisa multi-timeframe (Weekly, Daily, H4, H1, M15) buat major forex pairs,
kombinasi RSI + MACD + Bollinger Bands + EMA Cross + VWAP. Kirim sinyal
BUY/SELL otomatis ke Telegram kalau ada confluence (kesearahan) yang kuat.

⚠️ **Bukan nasihat keuangan.** Ini alat bantu analisa teknikal otomatis,
bukan rekomendasi trading. Forex berisiko tinggi (leverage, volatilitas
tinggi) — selalu pakai manajemen risiko & verifikasi manual.

## Struktur
- `config.py` — daftar pair, bobot timeframe, parameter indikator
- `indicators.py` — RSI, MACD, Bollinger Bands, EMA, VWAP, ATR
- `mtf_analysis.py` — ambil data & hitung bias tiap timeframe
- `signal_engine.py` — gabungin semua jadi sinyal BUY/SELL + level trading
- `telegram_notify.py` — format & kirim notifikasi
- `main.py` — entry point
- `.github/workflows/forex_signal.yml` — jadwal otomatis tiap 30 menit

## Cara kerja sinyalnya

1. **Bias Multi-Timeframe**: tiap pair dianalisa di 5 timeframe (W/D/H4/H1/M15),
   masing-masing dapet skor -1 (bearish) sampai +1 (bullish) dari kombinasi
   EMA trend + RSI + MACD histogram. Digabung jadi skor keseluruhan (weighted).

2. **Entry Trigger**: kalau bias keseluruhan cukup kuat (≥0.5 atau ≤-0.5),
   dicek kondisi entry di H1 — RSI di area yang masuk akal, EMA cross
   searah, posisi vs VWAP & Bollinger Bands.

3. **Sinyal keluar** kalau confluence (bias + entry trigger) searah semua.
   Kalau enggak, pair itu di-skip (gak ada notifikasi paksa).

4. **Level trading** dihitung pakai ATR (Average True Range) — Stop Loss =
   1.5x ATR, Take Profit 1/2/3 pakai rasio risk-reward 1.5x/2.5x/4x.

## Setup

### GitHub Secrets yang perlu diisi
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

(Bisa pakai bot Telegram yang sama dengan project saham, atau bikin bot baru
biar notifikasinya kepisah.)

### Test manual
Tab Actions → "Forex Signal Otomatis" → Run workflow.

## Keterbatasan yang perlu kamu tau
- **Bukan real-time murni** — cek tiap 30 menit, bukan instan
- Data H4 di-resample dari data H1 (yfinance gak punya H4 native)
- VWAP forex kurang akurat karena data volume dari yfinance seringkali kosong
  (forex OTC market) — fallback ke typical price average
- Threshold sinyal (RSI, bias minimum) masih basic, silakan disesuaikan di
  `config.py` sambil jalan & evaluasi hasilnya
