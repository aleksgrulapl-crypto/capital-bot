import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

SAFE_MODE = False   # Set to False when ready for real trades


# ---------------------------------------------------------
# EPIC MAPPING FUNCTION (required for Capital.com)
# ---------------------------------------------------------
def get_epic(symbol):
    # Special case: SK Hynix (Korean stock)
    if symbol.upper() in ["SKHY", "000660"]:
        return "000660.KS"

    # All US stocks follow <symbol>.US
    return f"{symbol.upper()}.US"


# ---------------------------------------------------------
# CAPITAL.COM AUTHENTICATION
# ---------------------------------------------------------
def capital_login():
    print("Starting Capital.com login...")

    api_key = os.getenv("API_KEY")
    email = os.getenv("API_EMAIL")
    password = os.getenv("API_PASSWORD")

    if not api_key or not email or not password:
        print("ERROR: Missing environment variables.")
        return None

    url = "https://api-capital.backend-capital.com/api/v1/session"

    headers = {
        "Content-Type": "application/json",
        "X-CAP-API-KEY": api_key
    }

    body = {
        "identifier": email,
        "password": password
    }

    try:
        r = requests.post(url, json=body, headers=headers)
    except Exception as e:
        print("Login request failed:", e)
        return None

    cst = r.headers.get("CST")
    xst = r.headers.get("X-SECURITY-TOKEN")

    if not cst or not xst:
        print("ERROR: CST or X-SECURITY-TOKEN missing.")
        print("Status:", r.status_code)
        print("Headers:", dict(r.headers))
        print("Body:", r.text)
        return None

    print("Login successful.")
    return {"CST": cst, "XST": xst}


tokens = capital_login()

if not tokens:
    print("FATAL: Could not authenticate. Bot will not start.")
else:
    print("Bot authenticated successfully. Ready for webhook.")


# ---------------------------------------------------------
# ORDER PLACEMENT FUNCTION
# ---------------------------------------------------------
def place_order(symbol, action, order_type, quantity):
    epic = get_epic(symbol)

    url = "https://api-capital.backend-capital.com/api/v1/positions"

    headers = {
        "Content-Type": "application/json",
        "CST": tokens["CST"],
        "X-SECURITY-TOKEN": tokens["XST"]
    }

    body = {
        "epic": epic,
        "direction": action.upper(),   # BUY or SELL
        "size": float(quantity),       # ensure numeric
        "orderType": order_type.upper()  # MARKET, LIMIT, STOP
    }

    print("Sending order:", body)

    try:
        r = requests.post(url, json=body, headers=headers)
        print("Order response:", r.status_code, r.text)
        return r.json()
    except Exception as e:
        print("Order failed:", e)
        return {"error": str(e)}
# ---------------------------------------------------------
# WEBHOOK HANDLER (POST)
# ---------------------------------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Webhook received:", data)

    required_fields = ["symbol", "action", "type", "quantity"]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    symbol = data["symbol"]
    action = data["action"]
    order_type = data["type"]
    quantity = data["quantity"]

    if SAFE_MODE:
        print("SAFE_MODE active — no trades will be placed.")
        return jsonify({"status": "received", "safe_mode": True}), 200

    result = place_order(symbol, action, order_type, quantity)
    return jsonify(result), 200


# ---------------------------------------------------------
# ROOT ENDPOINT (GET)
# ---------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "running"}), 200


# ---------------------------------------------------------
# RUN FLASK
# ---------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 500))
    app.run(host="0.0.0.0", port=port)
