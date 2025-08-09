from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self, market: str):
        self.market = market
        self.prices = []

    @abstractmethod
    def update(self, ticker_data: dict):
        """실시간 ticker 데이터 수신 시 호출"""
        pass

    @abstractmethod
    def should_buy(self) -> bool:
        """매수 조건 만족 여부"""
        pass

    @abstractmethod
    def should_sell(self) -> bool:
        """매도 조건 만족 여부"""
        pass
