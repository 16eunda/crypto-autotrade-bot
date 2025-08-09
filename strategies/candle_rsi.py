# strategies/candle_rsi.py

import requests
import pandas as pd

class CandleRSIStrategy:
    def __init__(self, market="KRW-BTC", unit=60):
        self.market = market
        self.unit = unit

    def fetch_rsi_with_time(self, period=14):
        url = f"https://api.upbit.com/v1/candles/minutes/{self.unit}?market={self.market}&count={period+1}"
        res = requests.get(url)
        data = res.json()

        df = pd.DataFrame(data)
        df = df.sort_values(by="candle_date_time_kst")

        # RSI 계산
        delta = df['trade_price'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        last_candle_time = df.iloc[-1]["candle_date_time_kst"]
        last_rsi = rsi.iloc[-1]

        return last_candle_time, round(last_rsi, 2)



############################ 1차 초안 ############################
# from services.candle import get_candles

# class CandleRSIStrategy:
#     def __init__(self, market: str, rsi_period: int = 14, unit: int = 60):
#         self.market = market
#         self.rsi_period = rsi_period
#         self.unit = unit  # 분 단위 (60=1시간봉)
#         self.rsi = None

#     def fetch_rsi(self):
#         candles = get_candles(self.market, unit=self.unit, count=self.rsi_period + 1)
#         if len(candles) <= self.rsi_period:
#             print("⚠️ 캔들 수 부족")
#             return None

#         closes = [float(c['trade_price']) for c in reversed(candles)]

#         gains = []
#         losses = []
#         for i in range(1, len(closes)):
#             change = closes[i] - closes[i - 1]
#             gains.append(max(change, 0))
#             losses.append(abs(min(change, 0)))

#         avg_gain = sum(gains) / self.rsi_period
#         avg_loss = sum(losses) / self.rsi_period or 1e-6

#         rs = avg_gain / avg_loss
#         rsi = 100 - (100 / (1 + rs))
#         self.rsi = round(rsi, 2)
#         return self.rsi

#     def should_buy(self):
#         rsi = self.fetch_rsi()
#         if rsi is None:
#             return False
#         print(f"[RSI] 현재 RSI: {rsi}")
#         return rsi < 30

#     def should_sell(self):
#         rsi = self.fetch_rsi()
#         if rsi is None:
#             return False
#         print(f"[RSI] 현재 RSI: {rsi}")
#         return rsi > 70
