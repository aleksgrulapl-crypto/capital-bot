import logging
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ---------------------------------------------------------
# LOGGING SETUP
# ---------------------------------------------------------
logging.basicConfig(
    filename='trade_log.txt',
    level=logging.INFO,
    format='%(asctime)s — %(levelname)s — %(message)s'
)

logging.info("Bot started successfully.")

# ---------------------------------------------------------
# CAPITAL.COM API SETTINGS
# ---------------------------------------------------------
API_KEY = "jdlT78Lrg6oCWERe"
BASE_URL = "https://api-capital.backend-capital.com"

HEADERS = {
    "X-CAP-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

# ---------------------------------------------------------
# SEND MARKET ORDER
# ---------------------------------------------------------
def send_market_order(side, market):
    logging.info(f"Sending {side} order for {market}")

    endpoint = f"{BASE_URL}/positions"
    payload = {
        "direction": side,
        "market": market,
        "size": 1,
        "orderType": "MARKET"
    }

    try:
        response = requests.post(endpoint, json=payload, headers=HEADERS)
        logging.info(f"API response: {response.text}")
        return response.json()
    except Exception as e:
        logging.error(f"Error sending order: {e}")
        return {"error": str(e)}

# ---------------------------------------------------------
# WEBHOOK RECEIVER
# ---------------------------------------------------------
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    logging.info(f"Received webhook: {data}")

    side = data.get("side")
    ticker = data.get("ticker")

    if side == "buy":
        result = send_market_order("BUY", ticker)
    elif side == "sell":
        result = send_market_order("SELL", ticker)
    else:
        logging.warning("Webhook ignored — no valid side provided.")
        result = {"status": "ignored"}

    logging.info(f"Order result: {result}")
    return jsonify(result)

# ---------------------------------------------------------
# RUN SERVER
# ---------------------------------------------------------
if __name__ == '__main__':
    logging.info("Starting Flask server...")
    app.run(host="0.0.0.0", port=5000)
