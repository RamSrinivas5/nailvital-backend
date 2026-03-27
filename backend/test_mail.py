import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "gummasrinivas8106@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "yscv ojuc maby aqhi")

def test_email():
    print(f"Testing connection to {SMTP_SERVER}:{SMTP_PORT}...")
    try:
        msg = MIMEText("This is a test email from NailVital AI.")
        msg['Subject'] = "SMTP Test"
        msg['From'] = SENDER_EMAIL
        msg['To'] = SENDER_EMAIL
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
        server.set_debuglevel(1)
        server.starttls()
        print("Logging in...")
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        print("Sending message...")
        server.send_message(msg)
        server.quit()
        print("\n✅ Test successful! Email sent to yourself.")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")

if __name__ == "__main__":
    test_email()
