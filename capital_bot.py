import logging
import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------
logging.basicConfig(
    filename='trade_log.txt',
    level=logging.INFO,
    format='%(asctime)s — %(levelname)s — %(message)s'
)

logging.info("Bot started with dynamic position sizing + SL/TP")

# ---------------------------------------------------------
# CAPITAL.COM API SETTINGS
# ---------------------------------------------------------
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api-capital.backend-capital.com"

HEADERS = {
    "X-CAP-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

# ---------------------------------------------------------
# GET ACCOUNT BALANCE
# ---------------------------------------------------------
def get_balance():
    try:
        r = requests.get(f"{BASE_URL}/accounts", headers=HEADERS)
        data = r.json()
        balance = float(data["balance"])
        logging.info(f"Account balance: {balance}")
        return balance
    except Exception as e:
        logging.error(f"Error fetching balance: {e}")
        return None

# ---------------------------------------------------------
# CALCULATE POSITION SIZE (20% OF BALANCE)
# ---------------------------------------------------------
def calculate_position_size(balance, price):
    money_to_use = balance * 0.20
    size = money_to_use / price
    logging.info(f"Calculated size: {size} using 20% of balance")
    return round(size, 4)

# ---------------------------------------------------------
# SEND MARKET ORDER WITH SL/TP
# ---------------------------------------------------------
def send_market_order(side, market, price):
    balance = get_balance()
    if balance is None:
        return {"error": "Balance fetch failed"}

    size = calculate_position_size(balance, price)

    # SL = 2%, TP = 10%
    if side.upper() == "BUY":
        sl = round(price * 0.98, 2)
        tp = round(price * 1.10, 2)
    else:
        sl = round(price * 1.02, 2)
        tp = round(price * 0.90, 2)

    payload = {
        "direction": side.upper(),
        "market": market,
        "size": size,
        "orderType": "MARKET",
        "stopLoss": {"level": sl},
        "takeProfit": {"level": tp}
    }

    logging.info(f"Sending order: {payload}")

    try:
        response = requests.post(f"{BASE_URL}/positions", json=payload, headers=HEADERS)
        logging.info(f"API response: {response.text}")
        return response.json()
    except Exception as e:
        logging.error(f"Order error: {e}")
        return {"error": str(e)}

# ---------------------------------------------------------
# WEBHOOK RECEIVER
# ---------------------------------------------------------
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    logging.info(f"Webhook received: {data}")

    side = data.get("side")
    ticker = data.get("ticker")
    price = float(data.get("price"))

    result = send_market_order(side, ticker, price)
    logging.info(f"Order result: {result}")

    return jsonify(result)

# ---------------------------------------------------------
# RUN SERVER
# ---------------------------------------------------------
if __name__ == '__main__':
    logging.info("Flask server starting...")
    app.run(host="0.0.0.0", port=5000)
