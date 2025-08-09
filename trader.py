import time
from services.upbit_api import UpbitAPI
from strategies.base import BaseStrategy

class Trader:
    def __init__(self, market: str, strategy: BaseStrategy, api: UpbitAPI,
                 krw_budget: float = 10000.0,
                 target_profit: float = 0.02):  # 2% 수익률 목표
        self.market = market
        self.strategy = strategy
        self.api = api
        self.krw_budget = krw_budget
        self.last_action = None
        self.last_order_time = 0
        self.entry_price = None  # 매수 체결가
        self.target_profit = target_profit

    def on_ticker(self, data: dict):
        if data['code'] != self.market:
            return

        self.strategy.update(data)

        now = time.time()
        if now - self.last_order_time < 10:
            return  # 최소 10초 간격 제한

        current_price = float(data['trade_price'])

        # 보유 상태일 경우 수익률 기반 매도
        if self.entry_price:
            profit_ratio = (current_price - self.entry_price) / self.entry_price
            print(f"[INFO] 수익률: {profit_ratio * 100:.2f}%")
            if profit_ratio >= self.target_profit:
                print("🎯 목표 수익률 도달, 매도 실행")
                self.sell()
                return

        # 전략 기반 매매
        if self.strategy.should_buy() and self.last_action != "buy":
            print("🟢 매수 신호 감지!")
            self.buy(current_price)

        elif self.strategy.should_sell() and self.last_action != "sell":
            print("🔴 매도 신호 감지!")
            self.sell()

    def buy(self, current_price: float):
        balance = self.api.get_balance()
        krw_balance = float(next((b['balance'] for b in balance if b['currency'] == 'KRW'), 0))

        if krw_balance < self.krw_budget:
            print("⚠️ KRW 부족. 현재 잔액:", krw_balance)
            return

        # API 주석처리: 실거래 막기
        # result = self.api.place_order(
        #     market=self.market,
        #     side="bid",
        #     volume=None,
        #     price=str(self.krw_budget),
        #     ord_type="price"
        # )
        print(f"[BUY] 매수 주문 (예상 진입가: {current_price})")
        self.last_action = "buy"
        self.last_order_time = time.time()
        self.entry_price = current_price

    def sell(self):
        balance = self.api.get_balance()
        currency = self.market.split("-")[1]
        coin_balance = float(next((b['balance'] for b in balance if b['currency'] == currency), 0))

        if coin_balance < 0.0001:
            print("⚠️ 코인 수량 부족. 현재 수량:", coin_balance)
            return

        # API 주석처리: 실거래 막기
        # result = self.api.place_order(
        #     market=self.market,
        #     side="ask",
        #     volume=str(coin_balance),
        #     price=None,
        #     ord_type="market"
        # )
        print(f"[SELL] 매도 주문 실행")
        self.last_action = "sell"
        self.last_order_time = time.time()
        self.entry_price = None  # 포지션 종료



############## 초안 코드 ##############

# import time
# from services.upbit_api import UpbitAPI
# from strategies.base import BaseStrategy

# class Trader:
#     def __init__(self, market: str, strategy: BaseStrategy, api: UpbitAPI,
#                  krw_budget: float = 10000.0):
#         self.market = market
#         self.strategy = strategy
#         self.api = api
#         self.krw_budget = krw_budget
#         self.last_action = None  # "buy", "sell", None
#         self.last_order_time = 0

#     def on_ticker(self, data: dict):
#         if data['code'] != self.market:
#             return

#         self.strategy.update(data)

#         now = time.time()
#         if now - self.last_order_time < 10:
#             return  # 최소 10초 간격 제한

#         if self.strategy.should_buy() and self.last_action != "buy":
#             print("🟢 매수 신호 감지!")
#             self.buy()

#         elif self.strategy.should_sell() and self.last_action != "sell":
#             print("🔴 매도 신호 감지!")
#             self.sell()

#     def buy(self):
#         balance = self.api.get_balance()
#         krw_balance = float(next((b['balance'] for b in balance if b['currency'] == 'KRW'), 0))

#         if krw_balance < self.krw_budget:
#             print("⚠️ KRW 부족. 현재 잔액:", krw_balance)
#             return

#         result = self.api.place_order(
#             market=self.market,
#             side="bid",
#             volume=None,
#             price=str(self.krw_budget),
#             ord_type="price"
#         )
#         print("[BUY ORDER SENT]", result)
#         self.last_action = "buy"
#         self.last_order_time = time.time()

#     def sell(self):
#         balance = self.api.get_balance()
#         currency = self.market.split("-")[1]
#         coin_balance = float(next((b['balance'] for b in balance if b['currency'] == currency), 0))

#         if coin_balance < 0.0001:  # 최소 주문 수량 조건
#             print("⚠️ 코인 수량 부족. 현재 수량:", coin_balance)
#             return

#         result = self.api.place_order(
#             market=self.market,
#             side="ask",
#             volume=str(coin_balance),
#             price=None,
#             ord_type="market"
#         )
#         print("[SELL ORDER SENT]", result)
#         self.last_action = "sell"
#         self.last_order_time = time.time()
