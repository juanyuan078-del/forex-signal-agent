# telegram_notify.py
# Format pesan sinyal forex & kirim ke Telegram.
# Pakai bot Telegram YANG SAMA/BEDA dengan punya saham, bebas -
# atur di GitHub Secrets: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

import os
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_message(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram token/chat_id belum diset, skip notifikasi.")
        print(text)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    resp = requests.post(url, json=payload, timeout=15)
    if resp.status_code != 200:
        print(f"Gagal kirim Telegram: {resp.status_code} - {resp.text}")


def format_signal_message(signal: dict) -> str:
    arrow = "🟢⬆️" if signal["direction"] == "BUY" else "🔴⬇️"
    levels = signal["levels"]
    mtf = signal["mtf_breakdown"]

    mtf_lines = []
    tf_order = ["W", "D", "H4", "H1", "M15"]
    for tf in tf_order:
        if tf in mtf:
            b = mtf[tf]
            mtf_lines.append(f"  {tf}: {b['label']} ({b['score']})")

    alasan_text = "\n".join([f"• {a}" for a in signal["alasan"]])

    return (
        f"{arrow} *{signal['pair']} — {signal['direction']}*\n\n"
        f"📊 *Bias Multi-Timeframe* (skor {signal['overall_bias']})\n"
        + "\n".join(mtf_lines) + "\n\n"
        f"🎯 *Level Trading*\n"
        f"Entry: `{levels['entry']}`\n"
        f"Stop Loss: `{levels['stop_loss']}`\n"
        f"TP1: `{levels['tp1']}` | TP2: `{levels['tp2']}` | TP3: `{levels['tp3']}`\n\n"
        f"🧠 *Alasan Sinyal*\n{alasan_text}\n\n"
        f"_Perhitungan teknikal otomatis (MACD+RSI+BB+EMA+VWAP), bukan nasihat "
        f"keuangan. Forex berisiko tinggi — selalu verifikasi manual & pakai "
        f"manajemen risiko._"
    )


def format_no_signal_message(pairs_checked: list[str]) -> str:
    pairs_text = ", ".join(pairs_checked)
    return (
        f"🔍 *[FOREX SCAN]*\n"
        f"Gak ada sinyal confluence kuat saat ini.\n"
        f"Pair dicek: {pairs_text}"
    )
