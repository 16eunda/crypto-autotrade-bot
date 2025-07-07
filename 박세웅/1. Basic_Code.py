# 6.Side_Project
import pdb
import pyupbit
import time
import datetime
import pprint
import logging
import pandas as pd
import pickle
import subprocess
from pathlib import Path
import traceback
import telegram # pip install python-telegram-bot, pip install asyncio
import asyncio # Telegram Bot 사용 시 RuntimeWarning: Enable tracemalloc to get the object allocation traceback 오류 때문에 사용
import os.path # 파일 존재 유무 확인에 사용 
import logging.handlers
import schedule
import sqlite3 # 2024.07.20 박세웅 : 추가
import slack_sdk



# 자동매매 대상 종목
# 사용자 지정 종목
GV_TICKERS = ["KRW-BTC", "KRW-XRP", "KRW-TRX", "KRW-XLM", "KRW-ADA", "KRW-DOGE", "KRW-RENDER", "KRW-NEAR"]

# 업비트 원화 시장 상장 종목 전체 
#GV_TICKERS = pyupbit.get_tickers("KRW")

# 시총 2000억 이상 종목들
#GV_TICKERS = ['KRW-TRX', 'KRW-AVAX', 'KRW-HBAR', 'KRW-BCH', 'KRW-PEPE', 'KRW-UNI', 'KRW-AAVE', 'KRW-NEAR', 'KRW-APT', 'KRW-ONDO', 'KRW-CRO', 'KRW-ETC', 'KRW-TRUMP', 'KRW-MNT', 'KRW-RENDER', 'KRW-ATOM', 'KRW-POL', 'KRW-ALGO', 'KRW-ARB', 'KRW-TIA', 'KRW-BONK', 'KRW-JUP', 'KRW-STX', 'KRW-EOS', 'KRW-SEI', 'KRW-IMX', 'KRW-INJ', 'KRW-VIRTUAL', 'KRW-GRT', 'KRW-USDC', 'KRW-THETA', 'KRW-WAL', 'KRW-USDT', 'KRW-IOTA', 'KRW-PENGU', 'KRW-SAND', 'KRW-ENS', 'KRW-BSV', 'KRW-PENDLE', 'KRW-FLOW', 'KRW-XTZ', 'KRW-JTO', 'KRW-MANA', 'KRW-PYTH', 'KRW-EGLD', 'KRW-AXS', 'KRW-MOVE', 'KRW-NEO', 'KRW-KAVA', 'KRW-ATH', 'KRW-DEEP', 'KRW-KAITO', 'KRW-W', 'KRW-CHZ', 'KRW-BEAM', 'KRW-COMP', 'KRW-USDT', 'KRW-AKT', 'KRW-BERA', 'KRW-JST', 'KRW-MINA', 'KRW-CTC', 'KRW-1INCH', 'KRW-ZRO', 'KRW-MEW', 'KRW-SAFE', 'KRW-GLM', 'KRW-TFUEL', 'KRW-ARKM', 'KRW-ZIL', 'KRW-BLUR', 'KRW-QTUM', 'KRW-MOCA', 'KRW-CKB', 'KRW-ASTR', 'KRW-ZRX', 'KRW-VTHO', 'KRW-BAT', 'KRW-CELO', 'KRW-GAS', 'KRW-LAYER', 'KRW-ZETA', 'KRW-STG', 'KRW-SC', 'KRW-POLYX', 'KRW-ANKR', 'KRW-DRIFT', 'KRW-UXLINK', 'KRW-ELF', 'KRW-T', 'KRW-VANA', 'KRW-XEM', 'KRW-GMT', 'KRW-MASK', 'KRW-ORCA', 'KRW-COW', 'KRW-ME', 'KRW-ONT', 'KRW-BIGTIME', 'KRW-SXP', 'KRW-STPT', 'KRW-USDC', 'KRW-ANIME', 'KRW-WAVES', 'KRW-HIVE', 'KRW-SNT', 'KRW-PUNDIX', 'KRW-ICX', 'KRW-G', 'KRW-BORA']


# 진행 라운드 
GV_SET_ROUND = 1

# 제외 리스트
GV_EXCLUDED_LIST = []

# 예외처리 리스트 
GV_EXCEPT_LIST = []

# 상승 가능성이 큰 종목 찾는 범위 => (month, week, day, minute 중에 중장기 전략을 위한 day로 선택) 
GV_FIND_SKYROCKET_RANGE = "day"

# 2024.05.15 박세웅 : 상승 가능성이 큰 리스트 전역 변수로 변경
GV_LIST_MOVING_AVERAGE = []

# GV_HOPE_PRICE_KRW : 주문희망금액
GV_HOPE_PRICE_KRW = 5000.0 # (단위 : 원)

# GV_HOPE_PRICE_KRW_PER : 순자산에서 매수할 % (1% = 0.01, 0.8% = 0.008) 
#GV_HOPE_PRICE_KRW_PER = 0.008
#GV_HOPE_PRICE_KRW_PER = 0.1 # 2024.02.28 박세웅 : 수정


# GV_VAT : 업비트 매수 수수료, 주문희망금액에 거래 수수료를 더해줘야함!!!!!(거래수수료 안빼주면 InsufficientFundsBid 오류 발생!)★★★★★★★★
GV_VAT = 0.0005 # (0.05% = 0.05 X 0.01)

# GV_ORDER_VAT : 주문희망금액으로 매수 시 발생 수수료 금액( GV_ORDER_VAT = GV_HOPE_PRICE_KRW X GV_VAT )
GV_ORDER_VAT = GV_HOPE_PRICE_KRW*GV_VAT

# 수수료를 포함한 총 주문 금액
GV_ORDER_PRICE_KRW = GV_HOPE_PRICE_KRW + GV_ORDER_VAT

# 파이업비트 객체 생성 => (Upbit API Key를 txt 파일에서 읽어오기)
f = open("D:\\OneDrive\\Programming\\Python\\Trading_Automation\\Main_Project\\tools.txt")
lines = f.readlines()
GV_ACCESS = lines[0].strip() #strip()으로 개행 제거 \n
GV_SECRET = lines[1].strip() #strip()으로 개행 제거 \n
f.close()
upbit = pyupbit.Upbit(GV_ACCESS, GV_SECRET) # Class instance, object


# 텔레그램 기능 구현
# 텔레그램 Token, ID 정보 가져오기
# f = open("D:\\OneDrive\\Programming\\Python\\Trading_Automation\\Main_Project\\tpdndql1_bot.txt")
# lines = f.readlines()
# # telegram.error.InvalidToken: Unauthorized 오류 시 BotFather에게 /newbot으로 봇 재생성하거나 /reboke로 토큰 재생성
# GV_TELEGRAM_TOKEN = lines[0].strip() #strip()으로 개행 제거 \n
# GV_TELEGRAM_ID = lines[1].strip() #strip()으로 개행 제거 \n
# f.close()

# # 텔레그램 메세지 전송 기능
# async def Send_Telegram_Message(Message): 

# 	#2023.11.04 : 객체 표기 추가
# 	Object_Message = "< GPT X 2.AuTra >\n\n" + Message
# 	try:
# 		bot = telegram.Bot(token = Telegram_Token)
# 		await bot.send_message(Telegram_ID, Object_Message)
# 	except:
# 		print("Exception handling occurred in Telegram message transmission")
# 		#GV_OBJ_LOGGER.info("Exception handling occurred in Telegram message transmission.")
# 		print("") 


# Slack 메세지 전송
f = open("D:\\OneDrive\\Programming\\Python\\Trading_Automation\\Main_Project\\Slack_Channel.txt")
lines = f.readlines()
SLACK_TOKEN = lines[0].strip() #strip()으로 개행 제거 \n
SLACK_CHANNEL = '#3-암호화폐-관련정보-공유'

def Send_Slack_Message(slack_Message):
	slack_token = SLACK_TOKEN
	channel = SLACK_CHANNEL
	client = slack_sdk.WebClient(token = slack_token)
	client.chat_postMessage(channel = channel, text = slack_Message)




def get_macd_signal(df):
    short_ema = df['close'].ewm(span=12, adjust=False).mean()
    long_ema = df['close'].ewm(span=26, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def check_buy_signal(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="minute1", count=50)
    macd, signal = get_macd_signal(df)
    price = pyupbit.get_current_price(ticker)
    mov = df['close'].rolling(window=20).mean()

    if macd.iloc[-2] < signal.iloc[-2] and macd.iloc[-1] > signal.iloc[-1] and price > mov.iloc[-1]:
        return True, price
    return False, price

def buy(ticker, price):
    krw_balance = upbit.get_balance("KRW")
    if krw_balance > GV_ORDER_PRICE_KRW:
        upbit.buy_market_order(ticker, GV_ORDER_PRICE_KRW)
        print(f"[{datetime.datetime.now()}]\n매수: {ticker}\n금액 : {price:.0f}원")
        #asyncio.run(Send_Telegram_Message(f"[{datetime.datetime.now()}] 매수: {ticker} @ {price:.0f}원"))
        Send_Slack_Message(f"[{datetime.datetime.now()}] 매수: {ticker} @ {price:.0f}원")

def sell(ticker, price):
    amount = upbit.get_balance(ticker)
    if amount:
        #upbit.sell_market_order(ticker, amount * 0.9995)
        upbit.sell_market_order(ticker, amount)
        print(f"[{datetime.datetime.now()}]\n매도: {ticker}\n금액 : {price:.0f}원")
        #asyncio.run(Send_Telegram_Message(f"[{datetime.datetime.now()}] 매도: {ticker} @ {price:.0f}원"))
        Send_Slack_Message(f"[{datetime.datetime.now()}] 매도: {ticker} @ {price:.0f}원")

def main_task():
    global GV_SET_ROUND

    print(f"Start round : {GV_SET_ROUND}")
    GV_SET_ROUND += 1

    for ticker in GV_TICKERS:
        try:
            signal, price = check_buy_signal(ticker)
            now_price = pyupbit.get_current_price(ticker)
            average_price = upbit.get_avg_buy_price(ticker)  # 매수 평균가

            if signal and average_price == 0:
                buy(ticker, price)
            elif price >= average_price * 1.05:
                sell(ticker, price)
            # 손절 코드 제외
        except Exception as e:
            print(f"[{ticker} 에러] {e}")
            continue

    print("작업 완료.")

# =============================================
# 매일 9시 1분에 한 번만 실행
# =============================================
print("자동 매매 스케줄러 시작됨. 매일 9시 1분에 실행됩니다.")
GV_SET_ROUND = 1
GV_EXCEPT_LIST = []

while True:
    now = datetime.datetime.now()
    # 9시 1분 0초에 시작
    if now.hour == 9 and now.minute == 1:
        main_task()

        # 다음 날까지 대기 (60초 단위로 확인)
        while True:
            time.sleep(60)
            now = datetime.datetime.now()
            if now.hour != 9 or now.minute != 1:
                break
    else:
        time.sleep(30)  # 대기 간격 조절 가능 (자원 절약)
	







