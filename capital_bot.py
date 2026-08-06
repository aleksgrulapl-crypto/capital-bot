from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Load Capital.com API key from Render environment variable
CAPITAL_API_KEY = os.getenv("CAPITAL_API_KEY")

CAPITAL_API_URL = "https://api-capital.backend-capital.com/api/v1/orders"

headers = {
    "X-CAP-API-KEY": CAPITAL_API_KEY,
    "Content-Type": "application/json"
}

def send_order(symbol, action, quantity):
    payload = {
        "symbol": symbol,
        "action": action,
        "type": "market",
        "quantity": quantity
    }

    print("Sending order payload:", payload)

    try:
        response = requests.post(CAPITAL_API_URL, json=payload, headers=headers)
        print("Raw Capital.com response:", response.text)
        return response.json()
    except Exception as e:
        print("Error sending order:", e)
        return {"status": "error", "message": str(e)}


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("Incoming JSON:", data)

        # Validate required fields
        required = ["symbol", "action", "type", "quantity"]
        for field in required:
            if field not in data:
                print(f"Missing field: {field}")
                return jsonify({"error": f"Missing field: {field}"}), 400

        symbol = data["symbol"]
        action = data["action"]
        quantity = data["quantity"]

        print(f"Received order → {symbol} | {action} | qty={quantity}")

        # Send order to Capital.com
        result = send_order(symbol, action, quantity)

        print("Capital.com response:", result)

        return jsonify(result)

    except Exception as e:
        print("Webhook error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return "Capital.com Trading Bot is running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
