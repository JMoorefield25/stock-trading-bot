import time
import requests
from alpaca_trade_api.rest import REST, TimeFrame

# 🔑 Alpaca and Telegram Credentials
API_KEY = "PKYUV28LDGQWXGMZ7OGM"
API_SECRET = "MGKIxVzlI1h1WCwffA18Up9RScNgimLhR7nPx3Sd"
TELEGRAM_BOT_TOKEN = "7560329215:AAHHZ2N-T5XSa0RGknRi9m_2QioGF7icga8"
CHAT_ID = "7126195607"

# 🔌 Connect to Alpaca paper trading API
api = REST(API_KEY, API_SECRET, base_url="https://paper-api.alpaca.markets")

# 📲 Function to send Telegram messages
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    response = requests.post(url, data=payload)
    print("Telegram Response:", response.json())

# 📊 Get moving averages
def get_moving_averages(symbol, short_window=5, long_window=20):
    bars = api.get_bars(symbol, TimeFrame.Minute, limit=long_window).df
    short_ma = bars['close'][-short_window:].mean()
    long_ma = bars['close'][-long_window:].mean()
    return short_ma, long_ma

# 🔁 Main trading logic
def trade_logic(symbol):
    position = None

    while True:
        try:
            short_ma, long_ma = get_moving_averages(symbol)
            last_price = api.get_latest_trade(symbol).price
            print(f"{symbol} | Price: {last_price} | Short MA: {short_ma} | Long MA: {long_ma}")

            if short_ma > long_ma and position != "long":
                api.submit_order(symbol=symbol, qty=1, side="buy", type="market", time_in_force="gtc")
                send_telegram_message(f"📈 Bought 1 share of {symbol} at ${last_price}")
                position = "long"

            elif short_ma < long_ma and position != "short":
                # ✅ Check position before trying to sell
                try:
                    pos = api.get_position(symbol)
                    if int(pos.qty) >= 1:
                        api.submit_order(symbol=symbol, qty=1, side="sell", type="market", time_in_force="gtc")
                        send_telegram_message(f"📉 Sold 1 share of {symbol} at ${last_price}")
                        position = "short"
                    else:
                        send_telegram_message(f"⚠️ Skipped selling {symbol} — no shares owned.")
                except:
                    send_telegram_message(f"⚠️ Skipped selling {symbol} — no position found.")

        except Exception as e:
            print("Error:", e)
            send_telegram_message(f"❌ Error: {e}")

        time.sleep(60)

# 🚀 Start the bot
if __name__ == "__main__":
    send_telegram_message("✅ Bot started successfully and is now running.")
    trade_logic("AAPL")  # Change symbol if you want to trade another stock