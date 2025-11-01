# src/finbot/reply_listener.py
import imaplib
import email
from email.header import decode_header
import os
from datetime import date
from typing import List
from .exec import execute_user_buys_for_date
import pickle

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
THREAD_SUBJECT_PREFIX = "FinBot – BUY at OPEN"

def _parse_tickers_from_text(text: str) -> List[str]:
    parts = [p.strip().upper() for p in text.replace(",", " ").split()]
    return [p for p in parts if p.isalnum() and len(p) <= 6]

def check_replies_and_execute(signals_dict, trade_date: date,
                              starting_cash=1_000, fee_bps=5, slippage_bps=1):
    user = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]

    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(user, app_password)
    mail.select("inbox")

    # search for emails from you (sent by you) with subject matching thread prefix
    # we assume you reply to the same thread so the subject might have Re: prefix
    status, data = mail.search(None,
                               f'(FROM "{user}" SUBJECT "{THREAD_SUBJECT_PREFIX} {trade_date.isoformat()}")')
    if status != "OK":
        print("No replies found")
        mail.logout()
        return

    for num in data[0].split():
        status, msg_data = mail.fetch(num, "(RFC822)")
        if status != "OK":
            continue
        msg = email.message_from_bytes(msg_data[0][1])
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8", errors="ignore")
        # get body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == "text/plain" and part.get_content_disposition() is None:
                    body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="ignore")

        tickers = _parse_tickers_from_text(body)
        if tickers:
            port, fills = execute_user_buys_for_date(signals_dict, tickers, trade_date,
                                                     starting_cash=starting_cash,
                                                     fee_bps=fee_bps, slippage_bps=slippage_bps)
            print("Executed fills:", fills)
        else:
            print("Reply found but no valid tickers parsed.")

        # optionally mark as seen/read or move to folder
    mail.logout()
