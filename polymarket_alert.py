import requests
import time
import os
from datetime import datetime

# ============================================================
#  APNI DETAILS YAHAN BHARO (ya Railway environment variables mein)
# ============================================================
WALLET_ADDRESS = os.environ.get("WALLET_ADDRESS", "0xYOUR_WALLET_ADDRESS_HERE")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")
CHECK_INTERVAL_SECONDS = 60
# ============================================================

DATA_API = "https://data-api.polymarket.com"

# Memory mein store karenge (file nahi)
seen_trade_ids = set()
first_run = True


def get_recent_trades():
    try:
        url = f"{DATA_API}/trades"
        params = {"user": WALLET_ADDRESS, "limit": 20}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[{now()}] API Error: {e}")
        return []


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        print(f"[{now()}] Telegram alert bheja!")
    except Exception as e:
        print(f"[{now()}] Telegram error: {e}")


def format_trade_alert(trade: dict) -> str:
    side = trade.get("side", "").upper()
    outcome = trade.get("outcome", "?")
    size = float(trade.get("size", 0))
    price = float(trade.get("price", 0))
    title = trade.get("title", "Unknown Market")
    total = size * price
    side_emoji = "🟢 BUY" if side == "BUY" else "🔴 SELL"

    return (
        f"🚨 <b>Polymarket Trade Alert!</b>\n\n"
        f"📊 <b>Market:</b> {title}\n"
        f"📌 <b>Outcome:</b> {outcome}\n"
        f"{side_emoji}\n"
        f"💰 <b>Amount:</b> {size:.2f} shares @ ${price:.3f}\n"
        f"💵 <b>Total:</b> ${total:.2f} USDC\n"
        f"🕐 <b>Time:</b> {now()}"
    )


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    global first_run, seen_trade_ids

    print(f"[{now()}] Polymarket Monitor shuru hua!")
    print(f"[{now()}] Wallet: {WALLET_ADDRESS}")

    send_telegram(
        f"✅ <b>Polymarket Alert Bot Shuru!</b>\n\n"
        f"👛 Wallet:\n<code>{WALLET_ADDRESS}</code>\n\n"
        f"⏱️ Har {CHECK_INTERVAL_SECONDS} second mein check hoga."
    )

    while True:
        try:
            trades = get_recent_trades()

            if first_run:
                # Pehli baar purani trades skip karo
                for trade in trades:
                    tid = trade.get("id") or trade.get("transactionHash", "")
                    if tid:
                        seen_trade_ids.add(tid)
                print(f"[{now()}] Pehli baar: {len(seen_trade_ids)} purani trades noted. Ab nai ka wait...")
                first_run = False
            else:
                new_trades = []
                for trade in trades:
                    tid = trade.get("id") or trade.get("transactionHash", "")
                    if tid and tid not in seen_trade_ids:
                        new_trades.append(trade)
                        seen_trade_ids.add(tid)

                if new_trades:
                    print(f"[{now()}] {len(new_trades)} nayi trade(s) mili!")
                    for trade in reversed(new_trades):
                        send_telegram(format_trade_alert(trade))
                        time.sleep(1)
                else:
                    print(f"[{now()}] Koi nayi trade nahi...")

        except Exception as e:
            print(f"[{now()}] Error: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
