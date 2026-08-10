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

tokens = {
    "CST": None,
    "XST": None,
    "available_equity": None,
    "balance_equity": None
}

# ---------------------------------------------------------
# LOGIN (CST + XST from HEADERS)
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

    print("[DEBUG] Login headers:", r.headers)
    print("[DEBUG] Login body:", r.text)

    if r.status_code == 200:
        body = r.json()

        # Extract tokens from HEADERS (Capital.com confirmed this)
        tokens["CST"] = r.headers.get("CST")
        tokens["XST"] = r.headers.get("X-SECURITY-TOKEN")

        # Extract real equity
        tokens["available_equity"] = body["accountInfo"]["available"]
        tokens["balance_equity"] = body["accountInfo"]["balance"]

        print("[INFO] Extracted CST:", tokens["CST"])
        print("[INFO] Extracted XST:", tokens["XST"])
        print("[INFO] Available equity:", tokens["available_equity"])
        print("[INFO] Balance equity:", tokens["balance_equity"])

        if tokens["CST"] and tokens["XST"]:
            print("[INFO] Login successful. Tokens updated.")
            return True

        print("[ERROR] Login succeeded but tokens missing.")
        return False

    print("[ERROR] Login failed:", r.text)
    return False


# ---------------------------------------------------------
# AUTH HEADERS
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
# AUTO-REFRESH TOKENS
# ---------------------------------------------------------
def ensure_tokens():
    if not tokens["CST"] or not tokens["XST"]:
        capital_login()


# ---------------------------------------------------------
# VERIFY EPIC
# ---------------------------------------------------------
def verify_epic(epic):
    print(f"[INFO] Verifying epic: {epic}")
    url = f"{BASE_URL}/api/v1/markets/{epic}"
    r = requests.get(url, headers=auth_headers())
    print("[DEBUG] Epic response:", r.text)
    return r.json()


# ---------------------------------------------------------
# MARKET STATUS
# ---------------------------------------------------------
def is_market_open(epic):
    data = verify_epic(epic)
    status = data.get("snapshot", {}).get("marketStatus", "")
    print(f"[INFO] Market status for {epic}: {status}")
    return status == "TRADEABLE"


# ---------------------------------------------------------
# POSITION SIZE (Option A — Available Equity)
# ---------------------------------------------------------
def calculate