# logic/trade.py

import pyupbit
from config import FEE_RATE, ORDER_KRW, PROFIT_THRESHOLD
from db.trades import log_trade
from notify.telegram import send_telegram
from logic.strategy import check_sell
import sqlite3
from config import DB_PATH

def buy(upbit, ticker):
    krw_balance = float(upbit.get_balance("KRW"))
    order_total = ORDER_KRW * (1 + FEE_RATE)

    if krw_balance < order_total:
        print(f"[SKIP] {ticker} - 잔액 부족 (현재 KRW: {krw_balance:.0f})")
        return

    price = pyupbit.get_current_price(ticker)
    amount = (ORDER_KRW * (1 - FEE_RATE)) / price
    upbit.buy_market_order(ticker, ORDER_KRW)
    log_trade("BUY", ticker, amount, price)
    send_telegram(f"[매수] {ticker} {amount:.4f}개 @ {price:,.0f} KRW")

def sell(upbit, ticker):
    symbol = ticker.replace("KRW-", "")
    amount = upbit.get_balance(symbol)
    price = pyupbit.get_current_price(ticker)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT price, volume FROM trades 
            WHERE ticker = ? AND action = 'BUY' ORDER BY id DESC LIMIT 1
        """, (ticker,))
        result = c.fetchone()

    if result:
        buy_price, volume = result
        df = pyupbit.get_ohlcv(ticker, interval="day", count=21)
        if check_sell(df, float(buy_price)):
            revenue = price * float(volume) * (1 - FEE_RATE)
            cost = float(buy_price) * float(volume)
            profit = revenue - cost
            return_rate = (profit / cost) * 100
            upbit.sell_market_order(ticker, amount)
            log_trade("SELL", ticker, float(volume), price, profit, return_rate)
            send_telegram(
                f"[매도] {ticker} {float(volume):.4f}개 @ {price:,.0f} KRW | "
                f"수익: {profit:,.0f}원 ({return_rate:.2f}%)"
            )
        else:
            print(f"[보유중] {ticker} → 수익률/중심선 조건 미충족")
    else:
        send_telegram(f"[매도 실패] {ticker} - 매수 정보 없음")
