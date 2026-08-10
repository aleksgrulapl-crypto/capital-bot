import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
BASE_URL = "https://api-capital.backend-capital.com"
API_KEY = os.getenv("API_KEY")
API_EMAIL = os.getenv("API_EMAIL")
API_PASSWORD = os.getenv("API_PASSWORD")

FIXED_EQUITY = float(os.getenv("ACCOUNT_EQUITY", 10000))

# Store tokens globally
tokens = {"CST": None, "XST": None}


# ---------------------------------------------------------
# LOGIN FUNCTION
# ---------------------------------------------------------
def capital_login():
    print("[INFO] Logging in to Capital.com...")
    url = f"{BASE_URL}/api/v1/session"

    payload = {
        "identifier": API_EMAIL,
        "password": API_PASSWORD,
        "encryptedPassword": False
    }

    headers = {
        "X-CAP-API-KEY": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "CapitalComPythonBot/1.0"
    }

    r = requests.post(url, json=payload, headers=headers)

    if r.status_code == 200:
        body = r.json()

        tokens["CST"] = body.get("CST")
        tokens["XST"] = body.get("securityToken")

        print("[INFO] Login successful. Tokens updated.")
        return True

    print("[ERROR] Login failed:", r.text)
    return False


# ---------------------------------------------------------
# STANDARD HEADERS (USED EVERYWHERE)
# ---------------------------------------------------------
def auth_headers():
    return {
        "X-CAP-API-KEY": API_KEY,
        "X-IG-API-KEY": API_KEY,
        "CST": tokens["CST"],
        "X-SECURITY-TOKEN": tokens["XST"],
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "CapitalComPythonBot/1.0"
    }


# ---------------------------------------------------------
# VERIFY EPIC FUNCTION
# ---------------------------------------------------------
def verify_epic(epic):
    print(f"[INFO] Verifying epic: {epic}")
    url = f"{BASE_URL}/api/v1/markets/{epic}"

    r = requests.get(url, headers=auth_headers())
    print("[DEBUG] Epic response:", r.text)

    return r.json()


# ---------------------------------------------------------
# MARKET STATUS CHECK
# ---------------------------------------------------------
def is_market_open(epic):
    data = verify_epic(epic)
    status = data.get("snapshot", {}).get("marketStatus", "")
    print(f"[INFO] Market status for {epic}: {status}")
    return status == "TRADEABLE"


# ---------------------------------------------------------
# POSITION SIZING
# ---------------------------------------------------------
def calculate_position_size(price, risk_fraction=0.20):
    equity = FIXED_EQUITY
    capital_to_use = equity * risk_fraction

    if price <= 0:
        print("[WARN] Invalid price received. Using fallback price=1.0")
        price = 1.0

    size = capital_to_use / price
    print(f"[INFO] Calculated position size: {size:.2f} units (Equity={equity}, Risk={risk_fraction}, Price={price})")
    return round(size, 2)


# ---------------------------------------------------------
# PLACE ORDER FUNCTION
# ---------------------------------------------------------
def place_order(epic, direction, size):
    print(f"[INFO] Placing order: epic={epic}, direction={direction}, size={size}")

    url = f"{BASE_URL}/api/v1/positions"

    payload = {
        "epic": epic,
        "direction": direction.upper(),
        "size": size,
        "orderType": "MARKET",
        "guaranteedStop": False
    }

    r = requests.post(url, json=payload, headers=auth_headers())
    print("[DEBUG] Order response:", r.text)

    if r.status_code == 200:
        return r.json()

    print("[ERROR] Order failed:", r.status_code, r.text)
    return {"error": r.text}


# ---------------------------------------------------------
# FLASK ROUTES
# ---------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return "Capital.com Trading Bot is live!", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("[INFO] Webhook received:", data)

    symbol = data.get("symbol", "EURUSD")
    action = data.get("action", "buy")

    # Ensure tokens are valid
    if not tokens["CST"] or not tokens["XST"]:
        capital_login()

    # Get price
    epic_data = verify_epic(symbol)
    price = epic_data.get("snapshot", {}).get("offer", 1.0)

    # Position size
    quantity = calculate_position_size(price)

    # Market check
    if not is_market_open(symbol):
        print(f"[INFO] Market closed for {symbol}. Skipping trade.")
        return jsonify({"error": f"Market closed for {symbol}"}), 200

    # Place order
    result = place_order(symbol, action, quantity)
    return jsonify(result), 200


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


# ---------------------------------------------------------
# STARTUP
# ---------------------------------------------------------
if __name__ == "__main__":
    if not capital_login():
        print("[FATAL] Authentication failed. Bot will not start.")
    else:
        print("[INFO] Bot authenticated successfully. Ready for webhook.")
        verify_epic("EURUSD")
