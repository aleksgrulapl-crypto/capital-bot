print("capital_bot.py LOADED SUCCESSFULLY")

from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# --- ENV VARS (set these in Render, NOT in code) ---
CAPITAL_API_KEY     = os.getenv("CAPITAL_API_KEY")
CAPITAL_IDENTIFIER  = os.getenv("CAPITAL_IDENTIFIER")  # your Capital.com login (email)
CAPITAL_PASSWORD    = os.getenv("CAPITAL_PASSWORD")    # your Capital.com password

CAPITAL_BASE_URL    = "https://api-capital.backend-capital.com"
SESSION_ENDPOINT    = f"{CAPITAL_BASE_URL}/api/v1/session"
POSITIONS_ENDPOINT  = f"{CAPITAL_BASE_URL}/api/v1/positions"


# --- LOGIN TO CAPITAL.COM ---
def capital_login():
    payload = {
        "identifier": CAPITAL_IDENTIFIER,
        "password": CAPITAL_PASSWORD,
        "encryptedPassword": False
    }

    headers = {
        "X-CAP-API-KEY": CAPITAL_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    print("Logging in to Capital.com...")
    resp = requests.post(SESSION_ENDPOINT, json=payload, headers=headers)
    print("Login status:", resp.status_code)
    print("Login raw response:", resp.text)

    if resp.status_code != 200:
        raise Exception(f"Login failed: {resp.text}")

    data = resp.json()

    cst = data.get("CST")
    xst = data.get("X-SECURITY-TOKEN")

    if not cst or not xst:
        raise Exception(f"Missing CST/X-SECURITY-TOKEN in login response: {data}")

    return cst, xst


# --- SEND ORDER TO CAPITAL.COM ---
def send_order(symbol, action, quantity):
    # Map TradingView action to Capital.com direction
    direction = action.upper()  # "BUY" / "SELL"

    # 1) Login to get tokens
    cst, xst = capital_login()

    # 2) Build order payload
    payload = {
        "epic": symbol,          # you may need to map this to Capital.com's EPIC
        "direction": direction,  # "BUY" or "SELL"
        "size": quantity,
        "orderType": "MARKET"
    }

    headers = {
        "X-CAP-API-KEY": CAPITAL_API_KEY,
        "CST": cst,
        "X-SECURITY-TOKEN": xst,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    print("Sending order payload:", payload)
    resp = requests.post(POSITIONS_ENDPOINT, json=payload, headers=headers)
    print("Order status:", resp.status_code)
    print("Order raw response:", resp.text)

    try:
        return resp.json()
    except Exception:
        return {"status": "error", "message": resp.text}


# --- WEBHOOK ---
@app.route("/webhook", methods=["POST"])
def webhook():
    print("Webhook endpoint was hit!")
    print("Raw request data:", request.data)

    try:
        data = request.get_json(silent=True)
        print("Incoming JSON:", data)

        if data is None:
            return jsonify({"error": "Invalid or empty JSON"}), 400

        required = ["symbol", "action", "type", "quantity"]
        for field in required:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        symbol   = data["symbol"]
        action   = data["action"]
        quantity = data["quantity"]

        print(f"Received order → {symbol} | {action} | qty={quantity}")

        result = send_order(symbol, action, quantity)
        print("Capital.com response (parsed):", result)

        return jsonify(result)

    except Exception as e:
        print("Webhook error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# --- HEALTH CHECK ---
@app.route("/", methods=["GET"])
def home():
    return "Capital.com Trading Bot is running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
