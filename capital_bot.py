import requests
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

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


# --- SEND ORDER TO CAPITAL.COM ---
def send_order(symbol, action, quantity):
    # Map TradingView action to Capital.com direction
    direction = action.upper()  # "BUY" / "SELL"

    # 1) Login to get tokens
    cst, xst = capital_login()

    # 2) Build order payload
    epic = get_epic(symbol)

    payload = {
        "epic": epic,
        "direction": direction,
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