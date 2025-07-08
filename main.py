import os
import alpaca_trade_api as tradeapi
import time
import datetime
import requests

# 🔐 Load credentials from environment variables (safe for Railway)
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
BASE_URL = 'https://paper-api.alpaca.markets'

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# ⚙️ BOT SETTINGS
symbol = "AAPL"          # ← You can change this to "TSLA", "MSFT", etc.
qty = 1                  # Number of shares per trade
short_window = 20        # Short moving average
long_window = 50         # Long moving average
risk_limit_pct = 0.03    # 3% stop loss
profit_target_pct = 0.05 # 5% take profit
check_interval = 60      # Check every 60 seconds

# ✅ SETUP ALPACA API
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)

def get_price_data():
    bars = api.get_bars(symbol, '1Min', limit=long_window)
    return [bar.c for bar in bars]

def calculate_moving_averages(prices):
    short_ma = sum(prices[-short_window:]) / short_window
    long_ma = sum(prices[-long_window:]) / long_window
    return short_ma, long_ma

def get_position():
    try:
        pos = api.get_position(symbol)
        return float(pos.qty), float(pos.avg_entry_price)
    except:
        return 0, 0

def place_order(side):
    try:
        api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type='market',
            time_in_force='gtc'
        )
        send_telegram_message(f"{datetime.datetime.now()}: {side.upper()} order placed for {qty} share(s) of {symbol}.")
    except Exception as e:
        send_telegram_message(f"Order failed: {e}")

def strategy():
    prices = get_price_data()
    if len(prices) < long_window:
        print("Waiting for enough data...")
        return

    short_ma, long_ma = calculate_moving_averages(prices)
    current_price = prices[-1]
    position_qty, avg_price = get_position()

    print(f"{datetime.datetime.now()} | {symbol} | Price: {current_price:.2f} | Short MA: {short_ma:.2f} | Long MA: {long_ma:.2f}")

    if short_ma > long_ma and position_qty == 0:
        place_order('buy')

    elif position_qty > 0:
        gain_pct = (current_price - avg_price) / avg_price
        gain_dollars = (current_price - avg_price) * qty

        if gain_pct >= profit_target_pct:
            send_telegram_message(f"💰 Profit target hit: {gain_pct:.2%} (${gain_dollars:.2f}) — selling {qty} share(s) of {symbol}.")
            place_order('sell')

        elif gain_pct <= -risk_limit_pct:
            send_telegram_message(f"🔻 Stop loss hit: {gain_pct:.2%} (${gain_dollars:.2f}) — selling {qty} share(s) of {symbol}.")
            place_order('sell')

# 🔁 RUN LOOP
while True:
    strategy()
    time.sleep(check_interval)