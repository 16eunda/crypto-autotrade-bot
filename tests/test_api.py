import os
from dotenv import load_dotenv
from services.upbit_api import UpbitAPI

load_dotenv()

access_key = os.getenv("UPBIT_ACCESS_KEY")
secret_key = os.getenv("UPBIT_SECRET_KEY")

api = UpbitAPI(access_key, secret_key)

def test_get_markets():
    markets = api.get_markets()
    print("[✔] 마켓 수:", len(markets))
    print(markets[:2])  # 일부만 출력

def test_get_balance():
    balance = api.get_balance()
    print("[✔] 보유 자산 정보:")
    print(balance)

def test_get_orderbook():
    orderbook = api.get_orderbook(["KRW-BTC", "KRW-ETH"])
    print("[✔] BTC/ETH 호가 정보:")
    for item in orderbook:
        print(item['market'], ":", item['orderbook_units'][:1])  # 일부만 출력

if __name__ == "__main__":
    test_get_markets()
    test_get_balance()
    test_get_orderbook()
