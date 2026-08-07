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
