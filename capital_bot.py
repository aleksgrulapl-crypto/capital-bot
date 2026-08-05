from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

API_KEY = "jdlT78Lrg6oCWERe"
BASE_URL = "https://api-capital.backend-capital.com"

HEADERS = {
    "X-CAP-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

def send_market_order(side, market):
    endpoint = f"{BASE_URL}/positions"
    
    payload = {
        "direction": side,
        "market": market,
        "size": 1,
        "orderType": "MARKET"
    }

    response = requests.post(endpoint, json=payload, headers=HEADERS)
    return response.json()

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Received:", data)

    side = data.get("side")
    ticker = data.get("ticker")

    if side == "buy":
        result = send_market_order("BUY", ticker)
    elif side == "sell":
        result = send_market_order("SELL", ticker)
    else:
        result = {"status": "ignored"}

    print("Order result:", result)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
