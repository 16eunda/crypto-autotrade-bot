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

# 매수 조건 거래량 
GV_TRANSACTION_VOLUME_CONDITIONS = 5

# 매수에 필요한 잔고 유무
GV_KRW_BALANCE_YN = True

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



# Buy DB
def InsertBuyDB(ticker, Average_vol, TransactionVolCond, Now_vol,  Atmosphere, TargetProfitRate):
	try: 
		#2024.07.20 박세웅 : Table 유무 확인 및 생성 
		conn = sqlite3.connect("D:\\Python_Test\\Side_Project\\박세웅\\Buy.db")
		conn.execute('pragma journal_mode=wal')
		cur = conn.cursor()
		CreateQuery = ""
		conn.execute('CREATE TABLE IF NOT EXISTS BuyT(\n '
						'KeyNo 				INTEGER PRIMARY KEY AUTOINCREMENT,\n '
						'CurrentTime 		INTEGER,\n '
						'TickerName 		TEXT,\n '
						'AverageVol 		INTEGER,\n '
						'TransactionVolCond INTEGER, \n '
						'NowVol 			REAL,\n '
						'Atmosphere 		TEXT,\n '
						'TargetProfitRate	REAL)')

		#2024.07.20 박세웅 : DB에 데이터 INSERT
		Query = "INSERT INTO BuyT (CurrentTime, TickerName, AverageVol, TransactionVolCond, NowVol, Atmosphere, TargetProfitRate) VALUES (datetime('now', 'localtime'), '{0}', {1}, {2}, {3}, '{4}', {5});".format(ticker, Average_vol, TransactionVolCond, Now_vol, Atmosphere, TargetProfitRate)		
		cur.execute(Query)
		conn.commit()
		conn.close()
	except:
		print("InsertBuyDB Error!")

		
# 2023.10.10 박세웅 추가 : 일봉 x% 이상 상승했는지 확인하는 기능
GV_DAY_INCREASE_RATE_NOT_EXCEEDED = 10 # 인상률 미초과
GV_DAY_INCREASE_RATE_EXCEEDED = 20	 # 인상률 초과
def day_increase_rate(df, ticker): 
	global GV_DAY_INCREASE_RATE_NOT_EXCEEDED
	global GV_DAY_INCREASE_RATE_EXCEEDED

	df1 = df.iloc[-1]
	last_open_price = df1['open']
	cur_price = pyupbit.get_current_price(ticker)

	increase_rate = ((cur_price - last_open_price)/last_open_price)*100

	if increase_rate > 5: # 현재 금액이 당일 open 가격보다 5% 초과로 상승했으면 return False
		return GV_DAY_INCREASE_RATE_EXCEEDED
	else:
		return GV_DAY_INCREASE_RATE_NOT_EXCEEDED



def Make_df_Add_Average_Volume(ticker, interval, rolling_value, count=20):
	# """
	# 거래량 평균이 추가된 데이터프레임
	# :param ticker: 캔들 정보를 표시할 코인
	# :param interval: 캔들정보 1분, 10분, 등..
	# :param rolling_value: 이동평균 갯수
	# :param count: 서버에서 취득할 데이터 수
	# :return: pandas dataframe
	# """
	try:
		df = pyupbit.get_ohlcv(ticker, interval, count=count)

		df['average'] = df['volume'].rolling(window=rolling_value).mean().shift(1)
		return df
	except:
		#asyncio.run(Send_Telegram_Message("Make_df_Add_Average_Volume에서 예외처리가 발생했습니다."))
		return 1

GV_GRAPH_UP = 10
GV_GRAPH_DOWN = 20
def is_up_or_down(df):  # 등락 구분
	global GV_GRAPH_UP
	global GV_GRAPH_DOWN

	# 2023.10.09 박세웅 : FutureWarning: Series.__getitem__ treating keys as positions is deprecated. 
	# In a future version, integer keys will always be treated as labels (consistent with DataFrame behavior). 
	# To access a value by position, use `ser.iloc[pos]` 오류로 아래와 같이 수정
	# 수정부분
	# last_close = df['close'][-1]
	# last_open_price = df['open'][-1]
	df1 = df.iloc[-1]
	last_close_1 = df1['close']
	last_open_price_1 = df1['open']

	df2 = df.iloc[-2]
	last_close_2 = df2['close']
	last_open_price_2 = df2['open']

	# 2023.11.06 박세웅 2분 동안 가격이 올랐으면 상승 중이라 판단
	# df3 = df.iloc[-3]
	# last_close_3 = df3['close']
	# last_open_price_3 = df3['open']

	# df4 = df.iloc[-4]
	# last_close_4 = df4['close']
	# last_open_price_4 = df4['open']

	# df5 = df.iloc[-5]
	# last_close_5 = df5['close']
	# last_open_price_5 = df5['open']
#####################################################
	# df6 = df.iloc[-6]
	# last_close_6 = df6['close']
	# last_open_price_6 = df6['open']

	# df7 = df.iloc[-7]
	# last_close_7 = df7['close']
	# last_open_price_7 = df7['open']

	# df8 = df.iloc[-8]
	# last_close_8 = df8['close']
	# last_open_price_8 = df8['open']

	# df9 = df.iloc[-9]
	# last_close_9 = df9['close']
	# last_open_price_9 = df9['open']

	# df10 = df.iloc[-10]
	# last_close_10 = df10['close']
	# last_open_price_10 = df10['open']
	
	increase_count = 0

	if last_close_1 - last_open_price_1 > 0:
		increase_count += 1
	if last_close_2 - last_open_price_2 > 0:
		increase_count += 1
	# 2023.11.06 박세웅 2분 동안 가격이 올랐으면 상승 중이라 판단
	# if last_close_3 - last_open_price_3 > 0:
	#	 increase_count += 1
	# if last_close_4 - last_open_price_4 > 0:
	#	 increase_count += 1
	# if last_close_5 - last_open_price_5 > 0:
	#	 increase_count += 1
#####################################################	
	# if last_close_6 - last_open_price_6 > 0:
	#	 increase_count += 1
	# if last_close_7 - last_open_price_7 > 0:
	#	 increase_count += 1
	# if last_close_8 - last_open_price_8 > 0:
	#	 increase_count += 1
	# if last_close_9 - last_open_price_9 > 0:
	#	 increase_count += 1
	# if last_close_10 - last_open_price_10 > 0:
	#	 increase_count += 1

	#2023.10.10 박세웅 상승 구분 조건 세분화
	# if last_close_1 - last_open_price_1 > 0 and last_close_2 - last_open_price_2 > 0 and last_close_3 - last_open_price_3 > 0:
	#	 return GV_GRAPH_UP
	# else:
	#	 return GV_GRAPH_DOWN

	# 2023.11.06 박세웅 2분 동안 가격이 올랐으면 상승 중이라 판단
	#if increase_count > 3:
	if increase_count == 2:
		return GV_GRAPH_UP
	else:
		return GV_GRAPH_DOWN

def Buy_Process(ticker):
	
	global GV_KRW_BALANCE_YN # 함수 안에서는global 써줘야 멤버 변수 인식 한다! 안하면 UnboundLocalError: cannot access local variable 'GV_KRW_BALANCE_YN' where it is not associated with a value 오류 
	global GV_TOTAL_KRW
	global GV_DAY_INCREASE_RATE_NOT_EXCEEDED
	global GV_GRAPH_UP
	global GV_TRANSACTION_VOLUME_CONDITIONS

	try:
		if upbit.get_avg_buy_price(ticker) == 0: # 코인을 보유하지 않는다면 매수
			
			# 현재 보유한 원화 총액
			GV_TOTAL_KRW = upbit.get_balance("KRW")

			# 원화 사용 금액 제한 현재 : 원화 보유 금액이 설정한 매수금액 아래로 떨어지면 매수 불가 => 나중에 알림 기능 넣기!
			if GV_TOTAL_KRW < GV_ORDER_PRICE_KRW:
			#if GV_TOTAL_KRW < 30000000000: # TEST 
				print("The money is not enough")
				#GV_OBJ_LOGGER.info("The money is not enough")
				
				if GV_KRW_BALANCE_YN == True:
					Message = "매수를 위한 원화 잔고가 부족합니다.\n(현재 원화 잔고 : {0}원)".format(format(round(GV_TOTAL_KRW), ','))
					#asyncio.run(Send_Telegram_Message(Message))
					GV_KRW_BALANCE_YN = False

				time.sleep(2)
				return False
			else:
				if GV_KRW_BALANCE_YN == False:
					Message = "원화 잔고가 입금되어 매수를 재시작합니다.\n(현재 원화 잔고 : {0}원)".format(format(round(GV_TOTAL_KRW), ','))
					#asyncio.run(Send_Telegram_Message(Message))			 
					GV_KRW_BALANCE_YN = True
		
			# 1분봉 이전 평균 10개
			data_count = 20 # 20개 데이터만 추출
			add_average_min_df = Make_df_Add_Average_Volume(ticker, "minute1", rolling_value=10, count=data_count)
			add_average_day_df = Make_df_Add_Average_Volume(ticker, "day", rolling_value=10, count=data_count)

			# 2023.10.09 박세웅 : Series.__getitem__ treating keys as positions is deprecated. 
			# In a future version, integer keys will always be treated as labels (consistent with DataFrame behavior). To access a value by position, use `ser.iloc[pos]`
			# now_vol = add_average_min_df['volume'][data_count-1] 오류로 아래와 같이 수정
			# 수정부분
			# average_vol = add_average_min_df['average'][data_count-1]
			# now_vol = add_average_min_df['volume'][data_count-1]
			df1 = add_average_min_df.iloc[-1]
			average_vol = df1['average']
			now_vol = df1['volume']

			# 일봉 상승률 초과 여부 판단
			increase_rate = day_increase_rate(add_average_day_df, ticker)
			if increase_rate == GV_DAY_INCREASE_RATE_NOT_EXCEEDED:
				# 양봉인지 판단
				up_down_value = is_up_or_down(add_average_min_df)
				if up_down_value == GV_GRAPH_UP: # 양봉인 경우 : 
					# 거래량 배수
					# 거래량이 적은경우 적은거래로도 튀기때문에 적은거래량에서는 20배만큼 상승해야 구매
					#compare_vol = average_vol * 7 #(거래량이 평균보다 7배 높을 시)
					compare_vol = average_vol * GV_TRANSACTION_VOLUME_CONDITIONS

					if now_vol >= compare_vol:

						#2023.10.17 박세웅 : 금일 17개 매도, 15,300원 수익으로 five_X_Candle_three_tic 조건 추가 일단 보류
						# 5일봉 3틱
						#up_down_value = five_X_Candle_three_tic(add_average_day_df)
						#if up_down_value == GV_GRAPH_DOWN: # 최근 5개의 X봉 중 음봉이 3개 이상일 경우


						# 구매 시그널
						#GV_ORDER_PRICE_KRW = GV_TOTAL_KRW * 0.1 # 보유 현금에서 10% 금액으로 매수 
						#GV_ORDER_PRICE_KRW = 20010
						#GV_VAT = (GV_ORDER_PRICE_KRW*0.0005) + 10 # 수수료(0.05%) 계산 후 + 10원 (10원은 혹시모를 패딩)
						#Purchase_Price = GV_ORDER_PRICE_KRW - GV_VAT

						buy_log = upbit.buy_market_order(ticker, GV_ORDER_PRICE_KRW) 
						#print('\033[30m', time.strftime('%m-%d %H:%M:%S'), ticker, " Purchase Completed")
						print(buy_log)
						#GV_OBJ_LOGGER.info(buy_log)
						Log = "{0} Purchase Completed".format(ticker)
						#GV_OBJ_LOGGER.info(Log)



						InsertBuyDB(ticker, round(average_vol), GV_TRANSACTION_VOLUME_CONDITIONS, round(now_vol), 'GV_REALTIME_ATMOSPHERE', 'GV_TARGET_PROFIT_RATE')



						if not buy_log:
							print("Failure To Buy ㅜ_ㅠ")
							#GV_OBJ_LOGGER.info("Failure To Buy")
				
			print("Waiting To Buy :", ticker)
			Log = "Waiting To Buy : {0}".format(ticker)
			#GV_OBJ_LOGGER.info(Log)
		# else:
		# 	Sell_Process(ticker)

	except:
		traceback_message = traceback.format_exc()
		print(traceback_message)






def main_task():
    global GV_SET_ROUND

    print(f"Start round : {GV_SET_ROUND}")
    GV_SET_ROUND += 1
	
    df_increase = []

    for ticker in GV_TICKERS:
        try:
            df = []
            df_day =  []
            yesterday_df = []
            AveragePrice = 0
            today_df = []


            df = pyupbit.get_ohlcv(ticker, "day", 100) # 원래 코드 
            # 데이터프레임에 30일 평균 close 가격인 AveragePrice 컬럼 추가
            df['AveragePrice'] = df['close'].rolling(window=30).mean().shift(1)				

            # 어제의 데이터프레임
            yesterday_df = df.iloc[-2] 

            # 어제까지의 과거 30일 평균 close 가격
            AveragePrice = yesterday_df['AveragePrice']

            # 오늘의 데이터프레임
            today_df = df.iloc[-1]

            #2024.07.20 박세웅 : 모든 종목의 총 거래량, 각 종목별 거래량 정보 저장을 위해 추가
            df_Minute = pyupbit.get_ohlcv(ticker, "minute1", 1)

            # 1분 단위 가장 최근 거래량
            df_Minute_LastRow = df_Minute.iloc[-1]
            Cur_Volume = df_Minute_LastRow['volume']
            df_Cur_Price = df_Minute_LastRow['close']


            # 오늘의 open 가격
            today_open_price = today_df['open']

            # 제한 상승률
            limit_rate = ((today_open_price - AveragePrice)/AveragePrice)*100

                
            #if limit_rate > 30: # 오늘 open 가격이 30일 동안 평균 close(종가) 가격보다 limit_rate(30%) 초과 시 제외 목록에 포함
            #if limit_rate > 20: # 2024.05.22 박세웅 : 20%로 수정
            if limit_rate > 50: # 2024.07.24 박세웅 : 30%에서 50%로 수정 
                GV_EXCLUDED_LIST.append(ticker)
                continue

            # 2023.10.25 박세웅 : 당일 open 가격이 0.001보다 작은 종목은 리스트에서 제외 조건 추가(현재 BTT 제외)
            if today_open_price < 0.001:
                GV_EXCLUDED_LIST.append(ticker)
                continue



            # 출처 : https://superhky.tistory.com/282
            # MACD가 Signal선보다 위쪽에 있으며 MACD 값은 하향이 아닌 상승을 하고 있어야 한다.
            # 또한 동시에 현재 가상화폐의 가격은 100일 EMA선보다 위쪽에 있어야 하고 20일 이동평균보다도 높아야 한다.
            # 끝으로 현재의 가상화폐 가격은 이전의 가격보다 높아야 한다.
            new_df = df['close']
            MOV = df['close'].rolling(window=20, min_periods=1).mean()
            ShortEMA = df.close.ewm(span=12, adjust=False).mean()
            LongEMA = df.close.ewm(span=26, adjust=False).mean()
            MACD = ShortEMA-LongEMA
            Signal = MACD.ewm(span=9, adjust=False).mean()
            EMA = df['close'].ewm(span=100, adjust=False).mean()
            price = pyupbit.get_current_price(ticker)

            # 2024.03.22 박세웅 : 현재 가격이 전날 종가보다 높아야하는 조건 삭제 and (price > new_df.iloc[-2] (장 시작 후 전날 종가 이하로 떨어졌다가 급상승하는 경우 잡기 위해 삭제함)
            #if (MACD.iloc[-1] > Signal.iloc[-1]) and (MACD.iloc[-1] > MACD.iloc[-2]) and (price > EMA.iloc[-1]) and (price > MOV.iloc[-1]) and (price > new_df.iloc[-2]):
            if (MACD.iloc[-1] > Signal.iloc[-1]) and (MACD.iloc[-1] > MACD.iloc[-2]) and (price > EMA.iloc[-1]) and (price > MOV.iloc[-1]):
                #df_increase.append(ticker)
                Buy_Process(ticker)

            time.sleep(1)

        except Exception as e:
            print(f"[{ticker} 에러] {e}")
            continue

    print("작업 완료.")

# =============================================
# 매일 9시 1분에 한 번만 실행
# =============================================
#print("자동 매매 스케줄러 시작됨. 매일 9시 1분에 실행됩니다.")


while True:
    main_task()
    time.sleep(600)  # 대기 간격 조절 가능 (자원 절약)
	







