# notify/telegram.py

import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg
    })
