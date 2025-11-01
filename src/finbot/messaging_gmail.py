import os 
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

def send_recos_email(tickers_to_buy,trade_date):
    sender = os.getenv("GMAIL_ADDRESS")
    app_password = os.getenv("GMAIL_APP_PASSWORD")
    recipient = os.getenv("USER_EMAIL")

    if not tickers_to_buy:
        subject = f"FinBot – No BUY signals {trade_date.isoformat()}"
        body = "No BUY signals for today."
    else:
        subject = f"FinBot – BUY at OPEN {trade_date.isoformat()}"
        body = "Today’s BUY list (execute at open):\n" + ", ".join(sorted(tickers_to_buy)) \
               + "\n\nReply to this email with the tickers you actually executed (CSV or space separated)."
        
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.login(sender, app_password)
        smtp.sendmail(sender, [recipient], msg.as_string())
    print("Sent email:", subject)