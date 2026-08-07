import requests
import os

def capital_login():
    url = "https://api-capital.backend-capital.com/api/v1/session"

    headers = {
        "Content-Type": "application/json",
        "X-CAP-API-KEY": os.getenv("API_KEY")
    }

    body = {
        "identifier": os.getenv("API_EMAIL"),
        "password": os.getenv("API_PASSWORD")
    }

    response = requests.post(url, json=body, headers=headers)

    # Extract tokens from HEADERS (not JSON)
    cst = response.headers.get("CST")
    xst = response.headers.get("X-SECURITY-TOKEN")

    if not cst or not xst:
        return {
            "error": "Authentication failed — CST or X-SECURITY-TOKEN missing",
            "status": response.status_code,
            "headers": dict(response.headers),
            "body": response.text
        }

    return {
        "CST": cst,
        "XST": xst
    }
