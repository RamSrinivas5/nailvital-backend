import random
import os
import requests
import traceback
from dotenv import load_dotenv

load_dotenv()

# Brevo HTTP API Configuration (Replaces SMTP)
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "gummasrinivas8106@gmail.com")
SENDER_NAME = "NailVital AI"

def generate_otp():
    return "".join([str(random.randint(0, 9)) for _ in range(6)])

def send_otp(email: str, otp: str):
    """
    Sends OTP via Brevo HTTP API to bypass Render SMTP blocks.
    """
    print(f"\n[OTP SERVICE] Attempting to send code {otp} to {email} via Brevo API...")
    
    if not BREVO_API_KEY:
        print("[OTP SERVICE] ❌ BREVO_API_KEY is not set. Cannot send email.")
        return

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    payload = {
        "sender": {
            "name": SENDER_NAME,
            "email": SENDER_EMAIL
        },
        "to": [
            {
                "email": email
            }
        ],
        "subject": "Your NailVital AI Verification Code",
        "htmlContent": f"<html><body><p>Hello,</p><p>Your verification code is: <strong>{otp}</strong></p><p>This code expires in 10 minutes.</p></body></html>"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 201:
            print(f"[OTP SERVICE] ✅ Email successfully sent to {email}")
        else:
            print(f"[OTP SERVICE] ❌ Brevo API Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"[OTP SERVICE] ❌ Network/Request Exception: {str(e)}")
        traceback.print_exc()
