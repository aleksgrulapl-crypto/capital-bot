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
