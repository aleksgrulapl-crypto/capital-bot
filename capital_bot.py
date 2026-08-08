import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

SAFE_MODE = True  # Set to False when ready for real trades

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
API_KEY = "LIVE_API_KEY_HERE"
IDENTIFIER = "LIVE_EMAIL_HERE"
PASSWORD = "LIVE_PASSWORD_HERE"
BASE_URL = "https://api-capital.backend-capital.com"

tokens = {"CST": None, "XST": None}

# ---------------------------------------------------------
# EPIC MAPPING FUNCTION
# ---------------------------------------------------------
def get_epic(symbol):
    if symbol.upper() in ["SKHY", "000660"]:
        return "000660.KS"
    return f"{symbol.upper()}.US"

# ---------------------------------------------------------
# LOGIN + TOKEN HANDLING
# ---------------------------------------------------------
def capital_login():
    print("Logging in to Capital.com...")
    url = f"{BASE_URL}/api/v1/session"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-CAP-API-KEY": API_KEY
    }
    body = {"identifier": IDENTIFIER, "password": PASSWORD, "encryptedPassword": False}

    try:
        r = requests.post(url, json=body, headers=headers)
        r.raise_for_status()
    except Exception as e:
        print("Login failed:", e)
        return None

    tokens["CST"] = r.headers.get("CST")
    tokens["XST"] = r.headers.get("X-SECURITY-TOKEN")

    if not tokens["CST"] or not tokens["XST"]:
        print("ERROR: Tokens missing in login response.")
        print("Response:", r.text)
        return None

    print("Login successful. Tokens updated.")
    return tokens

# ---------------------------------------------------------
# REQUEST WRAPPER WITH RETRY
# ---------------------------------------------------------
def capital_request(method, endpoint, payload=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-CAP-API-KEY": API_KEY,
        "CST": tokens["CST"],
        "X-SECURITY-TOKEN": tokens["XST"]
    }

    try:
        r = requests.request(method, url, json=payload, headers=headers)
        if r.status_code == 401:
            print("Session expired — refreshing tokens...")
            capital_login()
            headers["CST"] = tokens["CST"]
            headers["X-SECURITY-TOKEN"] = tokens["XST"]
            r = requests.request(method, url, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Request failed:", e)
        return {"error": str(e)}

# ---------------------------------------------------------
# ORDER PLACEMENT
# ---------------------------------------------------------
def place_order(symbol, action, order_type, quantity):
    epic = get_epic(symbol)
    payload = {
        "epic": epic,
        "direction": action.lower(),
        "size": quantity,
        "orderType": order_type.lower()
    }
    print("Placing order:", payload)
    return capital_request("POST", "/api/v1/positions", payload)

# ---------------------------------------------------------
# WEBHOOK HANDLER
# ---------------------------------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Webhook received:", data)

    required_fields = ["symbol", "action", "type", "quantity"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    if SAFE_MODE:
        print("SAFE_MODE active — trade skipped.")
        return jsonify({"status": "received", "safe_mode": True}), 200

    result = place_order(data["symbol"], data["action"], data["type"], data["quantity"])
    return jsonify(result), 200

# ---------------------------------------------------------
# ROOT ENDPOINT
# ---------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "running"}), 200

# ---------------------------------------------------------
# STARTUP
# ---------------------------------------------------------
if __name__ == "__main__":
    if not capital_login():
        print("FATAL: Authentication failed. Bot will not start.")
    else:
        print("Bot authenticated successfully. Ready for webhook.")
        port = int(os.environ.get("PORT", 500))
        app.run(host="0.0.0.0", port=port)
