import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

SAFE_MODE = True   # Set to False when ready for real trades


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
        "direction": action.lower(),   # buy or sell
        "size": quantity,
        "orderType": order_type.lower()  # market, limit, stop
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
# WEBHOOK HANDLER
# ---------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "running"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

