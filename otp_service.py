import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import os
from dotenv import load_dotenv

load_dotenv()

# SMTP Configuration (Injected from Environment Variables)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "gummasrinivas8106@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "yscv ojuc maby aqhi") 

def generate_otp():
    return "".join([str(random.randint(0, 9)) for _ in range(6)])

def send_otp(email: str, otp: str):
    """
    Sends OTP via Console (always) and Email (if configured)
    """
    print(f"\n[OTP SERVICE] Sent code {otp} to {email}\n")
    
    # Optional Email sending logic
    if "@" in SENDER_EMAIL and SENDER_PASSWORD != "your-app-password":
        try:
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = email
            msg['Subject'] = "Your NailVital AI Verification Code"
            
            body = f"Your verification code is: {otp}\n\nThis code expires in 10 minutes."
            msg.attach(MIMEText(body, 'plain'))
            
            print(f"[OTP SERVICE] Attempting to send email to {email} via {SMTP_SERVER}...")
            
            # Force IPv4 to fix Render 'Network is unreachable' error
            import socket
            smtp_ip = socket.gethostbyname(SMTP_SERVER)
            
            server = smtplib.SMTP(smtp_ip, SMTP_PORT, timeout=10)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            server.quit()
            print(f"[OTP SERVICE] ✅ Email successfully sent to {email}")
        except Exception as e:
            print(f"[OTP SERVICE] ❌ Failed to send email to {email}: {str(e)}")
            import traceback
            traceback.print_exc()
