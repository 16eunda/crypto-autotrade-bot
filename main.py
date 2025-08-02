import pyupbit, time
from datetime import datetime
from config import ACCESS, SECRET, TICKERS
from db.trades import init_db, already_bought_today
from logic.trade import buy, sell
from logic.strategy import check_buy
from notify.telegram import send_telegram

def run():
    upbit = pyupbit.Upbit(ACCESS, SECRET)
    init_db()
    round_no = 1

    while True:
        try:
            print(f"\n[Round {round_no}] 실행 중...")
            round_no += 1
            balances = upbit.get_balances()
            holding = {b['currency']: float(b['balance']) for b in balances if b['currency'] != 'KRW'}

            for ticker in TICKERS:
                df = pyupbit.get_ohlcv(ticker, interval="day", count=21)
                if df is None or len(df) < 21:
                    continue

                symbol = ticker.replace("KRW-", "")

                if symbol in holding and holding[symbol] > 0:
                    sell(upbit, ticker)
                elif not already_bought_today(ticker) and check_buy(df):
                    buy(upbit, ticker)
                else:
                    print(f"[관망중] {ticker} → 조건 미충족 또는 이미 매수함")

            time.sleep(3000)

        except Exception as e:
            print("에러 발생:", e)
            send_telegram(f"[에러 발생] {e}")
            time.sleep(3000)

if __name__ == "__main__":
    run()