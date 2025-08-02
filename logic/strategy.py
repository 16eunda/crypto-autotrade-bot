# logic/strategy.py

from config import PROFIT_THRESHOLD
from logic.indicator import get_bollinger, get_rsi

def check_buy(df):
    df = get_bollinger(df)
    df = get_rsi(df)

    #NaN 방지 : lower 또는 rsi에 결측치가 있으면 False
    if(df[["lower", "rsi"]].isnull().any().any()):
        return False
    try:
        return (
            df["close"].iloc[-2] < df["lower"].iloc[-2] and
            df["close"].iloc[-1] > df["lower"].iloc[-1] and
            df["rsi"].iloc[-1] <= 30
        )
    except IndexError:
        return False


    

def check_sell(df, buy_price):
    df = get_bollinger(df)

    # NaN 방지
    if df["ma"].isnull().any():
        return False
    
    try:
        current_price = df["close"].iloc[-1]
        ma = df["ma"].iloc[-1]
        return (
            current_price > ma and
            ((current_price - buy_price) / buy_price * 100) >= PROFIT_THRESHOLD
        )
    except IndexError:
        return False
    
    
#1. 처음 시작 시 (get_ohlcv가 21개 못 가져올 때)
#업비트 API에서 None을 반환하거나 21개 미만일 수 있음
#예: 네트워크 불안정, 특정 코인 거래량 적은 날, 서버 응답 문제 등

#2. 데이터가 중간에 비는 경우
#pyupbit.get_ohlcv()가 일부 날짜 데이터를 누락시킬 수 있음

#거래 중지된 종목 등에서 발생 가능

#3. 지표를 rolling(window=20)으로 계산하면
#처음 19개의 결과는 무조건 NaN임

#보통 count=21로 충분하지만, df.iloc[-1] 접근 시도에선 NaN이 있을 수도 있음