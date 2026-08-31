# main.py
# Entry point. Dipanggil GitHub Actions tiap 15-30 menit selama jam trading.

from config import FOREX_PAIRS
from signal_engine import run_forex_screening
from telegram_notify import send_message, format_signal_message, format_no_signal_message


def main():
    print("Menjalankan analisa forex multi-timeframe...")
    hasil = run_forex_screening()
    print(f"Ditemukan {len(hasil)} sinyal dari {len(FOREX_PAIRS)} pair yang dicek.")

    if not hasil:
        send_message(format_no_signal_message(list(FOREX_PAIRS.keys())))
        return

    for signal in hasil:
        pesan = format_signal_message(signal)
        send_message(pesan)
        print(f"Sinyal {signal['direction']} terkirim buat {signal['pair']}")


if __name__ == "__main__":
    main()
