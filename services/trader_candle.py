# services/trader_candle.py
import os
import time
import argparse
from dotenv import load_dotenv
from services.upbit_api import UpbitAPI
from strategies.candle_rsi import CandleRSIStrategy

TIMEFRAME_UNITS = {
    "30m": 30,
    "1h": 60,
    "4h": 240,
    "1d": "days",
}

class CandleTrader:
    def __init__(self, market="KRW-BTC", timeframe="1h",
                 buy_rsi=30, sell_rsi=70, target_profit=0.03, test_mode=False):

        load_dotenv()
        access_key = os.getenv("UPBIT_ACCESS_KEY") if not test_mode else "dummy_access"
        secret_key = os.getenv("UPBIT_SECRET_KEY") if not test_mode else "dummy_secret"

        self.market = market
        self.timeframe = timeframe
        self.unit = TIMEFRAME_UNITS[timeframe]
        self.buy_rsi = buy_rsi
        self.sell_rsi = sell_rsi
        self.target_profit = target_profit
        self.test_mode = test_mode

        self.api = UpbitAPI(access_key, secret_key)
        self.strategy = CandleRSIStrategy(market, self.unit)
        self.position = None

    def run(self):
        print(f"🚀 {self.timeframe} 캔들 기반 트레이더 시작: {self.market}")
        while True:
            last_candle_time, rsi = self.strategy.fetch_rsi_with_time()
            print(f"[RSI] {last_candle_time} 기준 RSI: {rsi}")

            current_price = self.api.get_current_price(self.market)
            if self.position is None and rsi <= self.buy_rsi:
                print("🟢 매수 신호!")
                self.position = {
                    "buy_price": current_price,
                    "buy_time": time.time()
                }
                if not self.test_mode:
                    self.api.place_order(self.market, "bid", 0.001, current_price, "limit")

            elif self.position:
                profit_ratio = (current_price - self.position["buy_price"]) / self.position["buy_price"]
                if profit_ratio >= self.target_profit or rsi >= self.sell_rsi:
                    print(f"🔴 매도 신호! (수익률: {profit_ratio:.2%})")
                    if not self.test_mode:
                        self.api.place_order(self.market, "ask", 0.001, current_price, "limit")
                    self.position = None

            if self.unit == "days":
                sleep_sec = 60 * 60 * 24
            else:
                sleep_sec = 60 * self.unit
            print(f"⏳ 다음 체크까지 {sleep_sec/60}분 대기...")
            time.sleep(sleep_sec)

def main():
    parser = argparse.ArgumentParser(description="Upbit Candle RSI Trader")
    parser.add_argument("--timeframe", type=str, default="1h",
                        choices=["30m", "1h", "4h", "1d"],
                        help="캔들 단위 선택 (30m, 1h, 4h, 1d)")
    parser.add_argument("--test_mode", action="store_true",
                        help="테스트 모드(주문 없이 로그만 출력)")
    args = parser.parse_args()

    trader = CandleTrader(
        timeframe=args.timeframe,
        test_mode=args.test_mode
    )
    trader.run()

if __name__ == "__main__":
    main()


################ 2차 초안 코드 ##################
# import os
# import time
# from dotenv import load_dotenv
# from services.upbit_api import UpbitAPI
# from strategies.candle_rsi import CandleRSIStrategy

# # 캔들 단위 매핑 (Upbit 기준)
# TIMEFRAME_UNITS = {
#     "30m": 30,    # 30분봉
#     "1h": 60,     # 1시간봉
#     "4h": 240,    # 4시간봉
#     "1d": "days", # 일봉
# }

# class CandleTrader:
#     def __init__(self, market="KRW-BTC", timeframe="1h",
#                  buy_rsi=30, sell_rsi=70, target_profit=0.03, test_mode=False):

#         load_dotenv()
#         access_key = os.getenv("UPBIT_ACCESS_KEY") if not test_mode else "dummy_access"
#         secret_key = os.getenv("UPBIT_SECRET_KEY") if not test_mode else "dummy_secret"

#         self.market = market
#         self.timeframe = timeframe
#         self.unit = TIMEFRAME_UNITS[timeframe]
#         self.buy_rsi = buy_rsi
#         self.sell_rsi = sell_rsi
#         self.target_profit = target_profit
#         self.test_mode = test_mode

#         self.api = UpbitAPI(access_key, secret_key)
#         self.strategy = CandleRSIStrategy(market, self.unit)
#         self.position = None

#     def run(self):
#         print(f"🚀 {self.timeframe} 캔들 기반 트레이더 시작: {self.market}")
#         while True:
#             rsi = self.strategy.fetch_rsi()
#             print(f"[RSI] 현재 RSI: {rsi}")

#             current_price = self.api.get_current_price(self.market)
#             if self.position is None and rsi <= self.buy_rsi:
#                 print("🟢 매수 신호!")
#                 self.position = {
#                     "buy_price": current_price,
#                     "buy_time": time.time()
#                 }
#                 if not self.test_mode:
#                     self.api.place_order(self.market, "bid", 0.001, current_price, "limit")

#             elif self.position:
#                 profit_ratio = (current_price - self.position["buy_price"]) / self.position["buy_price"]
#                 if profit_ratio >= self.target_profit or rsi >= self.sell_rsi:
#                     print(f"🔴 매도 신호! (수익률: {profit_ratio:.2%})")
#                     if not self.test_mode:
#                         self.api.place_order(self.market, "ask", 0.001, current_price, "limit")
#                     self.position = None

#             # 캔들 단위에 맞춰 대기
#             if self.unit == "days":
#                 sleep_sec = 60 * 60 * 24
#             else:
#                 sleep_sec = 60 * self.unit
#             print(f"⏳ 다음 체크까지 {sleep_sec/60}분 대기...")
#             time.sleep(sleep_sec)


# if __name__ == "__main__":
#     # 실행 옵션
#     trader = CandleTrader(
#         market="KRW-BTC",
#         timeframe="1h",      # "30m" / "1h" / "4h" / "1d" 선택 가능
#         buy_rsi=30,
#         sell_rsi=70,
#         target_profit=0.03,
#         test_mode=True       # True면 주문 안 하고 로그만 출력
#     )
#     trader.run()



################## 1차 초안 코드 ##################
# import os
# from dotenv import load_dotenv
# import time
# from datetime import datetime
# from services.upbit_api import UpbitAPI
# from strategies.candle_rsi import CandleRSIStrategy

# class CandleTrader:
#     def __init__(self, market="KRW-BTC", unit=60, buy_rsi=30, sell_rsi=70, target_profit=0.03):
#         load_dotenv()
#         access_key = os.getenv("UPBIT_ACCESS_KEY")
#         secret_key = os.getenv("UPBIT_SECRET_KEY")
        
#         self.market = market
#         self.unit = unit
#         self.buy_rsi = buy_rsi
#         self.sell_rsi = sell_rsi
#         self.target_profit = target_profit
#         self.api = UpbitAPI(access_key, secret_key)
#         self.strategy = CandleRSIStrategy(market, unit)
#         self.position = None  # {'price': float, 'volume': float}

#     def run(self):
#         print(f"[START] {self.unit}분봉 RSI 매매 시작")
#         last_checked_candle = None

#         while True:
#             # 현재 시각의 캔들 정보 가져오기
#             candle_time, rsi = self.strategy.fetch_rsi_with_time()

#             if candle_time != last_checked_candle:  # 새로운 캔들이 시작되었을 때만 매매 판단
#                 print(f"[{datetime.now()}] 새로운 캔들 ({self.unit}분) - RSI: {rsi:.2f}")
#                 last_checked_candle = candle_time

#                 if self.position is None:  # 보유 포지션이 없을 때 → 매수 판단
#                     if rsi <= self.buy_rsi:
#                         print("🟢 매수 신호 감지!")
#                         # volume = 0.001  # 예시
#                         # price = self.api.get_current_price(self.market)
#                         # self.api.place_order(self.market, "bid", volume, price, "limit")
#                         self.position = {"price": self.api.get_current_price(self.market), "volume": 0.001}
#                         print(f"✅ 매수 체결가: {self.position['price']}")
#                 else:  # 포지션 보유 중 → 매도 판단
#                     current_price = self.api.get_current_price(self.market)
#                     profit_ratio = (current_price - self.position["price"]) / self.position["price"]

#                     if profit_ratio >= self.target_profit or rsi >= self.sell_rsi:
#                         print(f"🔴 매도 신호 감지! 수익률: {profit_ratio*100:.2f}%")
#                         # self.api.place_order(self.market, "ask", self.position["volume"], current_price, "limit")
#                         self.position = None
#                         print("✅ 매도 완료")

#             time.sleep(10)  # 10초마다 확인 (캔들이 완성될 때까지 대기)

# if __name__ == "__main__":
#     trader = CandleTrader(market="KRW-BTC", unit=60, buy_rsi=30, sell_rsi=70, target_profit=0.03)
#     trader.run()
