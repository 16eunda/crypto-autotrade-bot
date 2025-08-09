import time
from strategies.base import BaseStrategy

class RSIStrategy(BaseStrategy):
    def __init__(self, market: str, rsi_period: int = 14, signal_interval_sec=1800):
        super().__init__(market)
        self.rsi_period = rsi_period
        self.last_rsi = None
        self.last_signal_time = 0
        self.signal_interval_sec = signal_interval_sec

    def update(self, ticker_data: dict):
        price = float(ticker_data['trade_price'])
        self.prices.append(price)

        if len(self.prices) > self.rsi_period + 1:
            self.prices.pop(0)
            self.last_rsi = self._calculate_rsi()

    def _calculate_rsi(self):
        gains, losses = [], []
        for i in range(1, len(self.prices)):
            change = self.prices[i] - self.prices[i - 1]
            gains.append(max(change, 0))
            losses.append(abs(min(change, 0)))

        avg_gain = sum(gains) / self.rsi_period
        avg_loss = sum(losses) / self.rsi_period or 1e-6

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)

    def should_buy(self) -> bool:
        now = time.time()
        if self.last_rsi is not None and self.last_rsi < 30 and now - self.last_signal_time > self.signal_interval_sec:
            self.last_signal_time = now
            return True
        return False

    def should_sell(self) -> bool:
        now = time.time()
        if self.last_rsi is not None and self.last_rsi > 70 and now - self.last_signal_time > self.signal_interval_sec:
            self.last_signal_time = now
            return True
        return False



################### 초안 코드 ###################
# from strategies.base import BaseStrategy

# class RSIStrategy(BaseStrategy):
#     def __init__(self, market: str, rsi_period: int = 14):
#         super().__init__(market)
#         self.rsi_period = rsi_period
#         self.last_rsi = None

#     def update(self, ticker_data: dict):
#         price = float(ticker_data['trade_price'])
#         self.prices.append(price)

#         if len(self.prices) > self.rsi_period + 1:
#             self.prices.pop(0)
#             self.last_rsi = self._calculate_rsi()

#     def _calculate_rsi(self):
#         gains = []
#         losses = []
#         for i in range(1, len(self.prices)):
#             change = self.prices[i] - self.prices[i - 1]
#             if change > 0:
#                 gains.append(change)
#                 losses.append(0)
#             else:
#                 gains.append(0)
#                 losses.append(abs(change))

#         avg_gain = sum(gains) / self.rsi_period
#         avg_loss = sum(losses) / self.rsi_period
#         if avg_loss == 0:
#             return 100  # RSI 최대치

#         rs = avg_gain / avg_loss
#         rsi = 100 - (100 / (1 + rs))
#         return round(rsi, 2)

#     def should_buy(self) -> bool:
#         return self.last_rsi is not None and self.last_rsi < 30

#     def should_sell(self) -> bool:
#         return self.last_rsi is not None and self.last_rsi > 70
