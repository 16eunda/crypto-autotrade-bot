# config.py

from dotenv import load_dotenv
import os

load_dotenv()  # .env 파일에서 환경변수 읽어오기

ACCESS = os.getenv("UPBIT_ACCESS")
SECRET = os.getenv("UPBIT_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DB_PATH = "bollinger_trades_safe.db"

FEE_RATE = 0.0005
ORDER_KRW = 10_000.0
ORDER_TOTAL = ORDER_KRW * (1 + FEE_RATE)  # = 10,005원

PROFIT_THRESHOLD = 3.0  # 최소 수익률 3%

TICKERS = [
    "KRW-BTC",
    "KRW-ETH",
    "KRW-XRP",
    "KRW-SOL",
    "KRW-MATIC"
]