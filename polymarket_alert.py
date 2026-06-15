import requests
import time
import os
from datetime import datetime

# ============================================================
#  TELEGRAM SETTINGS (Railway Variables se aayega)
# ============================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
CHECK_INTERVAL_SECONDS = 60

# ============================================================
#  TRACK KARNE WALE WALLETS
# ============================================================
WALLETS = {
    "0x6011655c4afb76f36dd1b08a137a1ba73466b31e": "👤 Mera Account",
    "0xb9012e0d9b60d3920286309328b935cdfa609fc4": "🕵️ Unknown #1",
    "0x36b236c2351e59c5620c2dc498b9baa2fbd05047": "🕵️ Unknown #2",
}

DATA_API = "https://data-api.polymarket.com"
seen_trade_ids = set()
first_run = True


def get_trades(wallet):
    try:
        resp = requests.get(f"{DATA_API}/trades",
            params={"user": wallet, "limit": 20}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[{now()}] API Error ({wallet[:8]}...): {e}")
        return []


def send_telegram(message):
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=10)
        resp.raise_for_status()
        print(f"[{now()}] Telegram alert bheja!")
    except Exception as e:
        print(f"[{now()}] Telegram error: {e}")


def format_trade(trade, wallet_name):
    side = trade.get("side", "").upper()
    size = float(trade.get("size", 0))
    price = float(trade.get("price", 0))
    return (
        f"🚨 <b>Polymarket Trade Alert!</b>\n\n"
        f"👛 <b>Wallet:</b> {wallet_name}\n"
        f"📊 <b>Market:</b> {trade.get('title', '?')}\n"
        f"📌 <b>Outcome:</b> {trade.get('outcome', '?')}\n"
        f"{'🟢 BUY' if side == 'BUY' else '🔴 SELL'}\n"
        f"💰 <b>Amount:</b> {size:.2f} @ ${price:.3f}\n"
        f"💵 <b>Total:</b> ${size * price:.2f} USDC\n"
        f"🕐 {now()}"
    )


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    global first_run, seen_trade_ids
    print(f"[{now()}] Bot shuru hua! {len(WALLETS)} wallets track ho rahe hain.")

    send_telegram(
        f"✅ <b>Polymarket Alert Bot Shuru!</b>\n\n"
        f"📡 <b>Track ho rahe hain:</b>\n"
        + "\n".join([f"• {name}: <code>{addr[:10]}...</code>" for addr, name in WALLETS.items()])
        + f"\n\n⏱️ Har {CHECK_INTERVAL_SECONDS}s mein check hoga."
    )

    while True:
        try:
            for wallet, name in WALLETS.items():
                trades = get_trades(wallet)

                if first_run:
                    for t in trades:
                        tid = t.get("id") or t.get("transactionHash", "")
                        if tid:
                            seen_trade_ids.add(tid)
                else:
                    new = []
                    for t in trades:
                        tid = t.get("id") or t.get("transactionHash", "")
                        if tid and tid not in seen_trade_ids:
                            new.append(t)
                            seen_trade_ids.add(tid)
                    if new:
                        print(f"[{now()}] {len(new)} nayi trade(s) - {name}")
                        for t in reversed(new):
                            send_telegram(format_trade(t, name))
                            time.sleep(1)

                time.sleep(2)  # Wallets ke beech thoda wait

            if first_run:
                print(f"[{now()}] Pehli baar: {len(seen_trade_ids)} purani trades noted.")
                first_run = False
            else:
                print(f"[{now()}] Check complete. Koi nayi trade nahi...")

        except Exception as e:
            print(f"[{now()}] Error: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
