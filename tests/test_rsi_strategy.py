from strategies.rsi_strategy import RSIStrategy
from services.websocket import WebSocketManager

strategy = RSIStrategy("KRW-BTC")

def handle_data(data):
    strategy.update(data)
    print(f"[RSI] 현재 RSI: {strategy.last_rsi}")
    if strategy.should_buy():
        print("💚 매수 신호 발생!")
    elif strategy.should_sell():
        print("❤️ 매도 신호 발생!")

if __name__ == "__main__":
    ws = WebSocketManager(
        markets=["KRW-BTC"],
        types=["ticker"],
        callback=handle_data
    )
    ws.run_forever()
