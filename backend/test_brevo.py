import os
import requests
API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = "gummasrinivas8106@gmail.com"
RECEIVER = "gummasrinivas8106@gmail.com"

url = "https://api.brevo.com/v3/smtp/email"
headers = {
    "accept": "application/json",
    "api-key": API_KEY,
    "content-type": "application/json"
}

payload = {
    "sender": {"name": "NailVital AI", "email": SENDER_EMAIL},
    "to": [{"email": RECEIVER}],
    "subject": "Test Brevo API",
    "htmlContent": "<p>This is a test.</p>"
}

print("Testing Brevo API...")
response = requests.post(url, json=payload, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
