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

# Store tokens globally
tokens = {"CST": None, "XST": None}


# ---------------------------------------------------------
# LOGIN FUNCTION
# ---------------------------------------------------------
def capital_login():
    print("Logging in to Capital.com...")
    url = f"{BASE_URL}/api/v1/session"
    payload = {
        "identifier": API_EMAIL,
        "password": API_PASSWORD,
        "encryptedPassword": False
    }
    headers = {
        "X-CAP-API-KEY": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    r = requests.post(url, json=payload, headers=headers)
    if r.status_code == 200:
        tokens["CST"] = r.headers.get("CST")
        tokens["XST"] = r.headers.get("X-SECURITY-TOKEN")
        print("Login successful. Tokens updated.")
        return True
    else:
        print("Login failed:", r.text)
        return False


# ---------------------------------------------------------
# VERIFY EPIC FUNCTION
# ---------------------------------------------------------
def verify_epic(epic):
    print(f"Verifying epic: {epic}")
    url = f"{BASE_URL}/api/v1/markets/{epic}"
    headers = {
        "X-CAP-API-KEY": API_KEY,
        "CST": tokens["CST"],
        "X-SECURITY-TOKEN": tokens["XST"],
        "Accept": "application/json"
    }
    r = requests.get(url, headers=headers)
    print("Response text:", r.text)
    return r.json()


# ---------------------------------------------------------
# PLACE ORDER FUNCTION
# ---------------------------------------------------------
def place_order(epic, direction, size):
    print(f"Placing order: {{'epic': '{epic}', 'direction': '{direction}', 'size': {size}, 'orderType': 'MARKET', 'guaranteedStop': False}}")

    url = f"{BASE_URL}/api/v1/positions"
    payload = {
        "epic": epic,
        "direction": direction.upper(),
        "size": size,
        "orderType": "MARKET",
        "guaranteedStop": False
    }
    headers = {
        "X-CAP-API-KEY": API_KEY,
        "CST": tokens["CST"],
        "X-SECURITY-TOKEN": tokens["XST"],
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    r = requests.post(url, json=payload, headers=headers)
    print("Response text:", r.text)
    if r.status_code == 200:
        return r.json()
    else:
        print("Request failed:", r.status_code, r.text)
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
    print("Webhook received:", data)

    symbol = data.get("symbol", "EURUSD")
    action = data.get("action", "buy")
    quantity = data.get("quantity", 1)

    if not tokens["CST"] or not tokens["XST"]:
        capital_login()

    verify_epic(symbol)
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
        print("FATAL: Authentication failed. Bot will not start.")
    else:
        print("Bot authenticated successfully. Ready for webhook.")
        verify_epic("EURUSD")
