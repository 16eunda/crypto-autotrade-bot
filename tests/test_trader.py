from trader import Trader
from strategies.rsi_strategy import RSIStrategy
from services.upbit_api import UpbitAPI
from services.websocket import WebSocketManager
import os
from dotenv import load_dotenv

load_dotenv()

api = UpbitAPI(
    os.getenv("UPBIT_ACCESS_KEY"),
    os.getenv("UPBIT_SECRET_KEY")
)

strategy = RSIStrategy("KRW-BTC")
trader = Trader("KRW-BTC", strategy, api, krw_budget=10000)

def handle_ticker(data):
    trader.on_ticker(data)

if __name__ == "__main__":
    ws = WebSocketManager(
        markets=["KRW-BTC"],
        types=["ticker"],
        callback=handle_ticker
    )
    ws.run_forever()
