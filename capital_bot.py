from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

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

    response = requests.post(CAPITAL_API_URL, json=payload, headers=headers)

    try:
        return response.json()
    except:
        return {"status": "error", "message": "Invalid JSON response from Capital.com"}

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("Incoming JSON:", data)   # ← ADD THIS

        required = ["symbol", "action", "type", "quantity"]
        for field in required:
            if field not in data:
                print(f"Missing field: {field}")  # ← ADD THIS
                return jsonify({"error": f"Missing field: {field}"}), 400

        symbol = data["symbol"]
        action = data["action"]
        quantity = data["quantity"]

        print(f"Received order → {symbol} | {action} | qty={quantity}")  # ← ADD THIS

        result = send_order(symbol, action, quantity)

        print("Capital.com response:", result)  # ← ADD THIS

        return jsonify(result)

    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
