# db/trades.py

import sqlite3
from datetime import datetime
from config import DB_PATH
from notify.telegram import send_telegram

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                ticker TEXT,
                volume REAL,
                price REAL,
                profit REAL,
                return_rate REAL,
                date TEXT
            )
        """)
        conn.commit()

def log_trade(action, ticker, volume, price, profit=None, return_rate=None):
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO trades (action, ticker, volume, price, profit, return_rate, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (action, ticker, volume, price, profit, return_rate, today))
            conn.commit()

    except sqlite3.Error as e:
        send_telegram(f"[로그 기록 실패] {e}")
        print(f"[로그 기록 실패] {e}")


def already_bought_today(ticker):
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("""SELECT 1 FROM trades 
                         WHERE action = 'BUY' AND ticker = ? AND date = ?""",
                      (ticker, today))
            return c.fetchone() is not None
    except sqlite3.Error as e:
        send_telegram(f"[오류 발생] 'already_bought_today' 함수에서 오류: {e}")
        print(f"[오류 발생] 'already_bought_today' 함수에서 오류: {e}")
        return False  # 오류가 나면 매수하지 않도록 False 반환