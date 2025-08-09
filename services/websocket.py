import websocket
import json
import threading
import time
from datetime import datetime

class WebSocketManager:
    def __init__(self, markets=["KRW-BTC"], types=["ticker"], callback=None):
        self.url = "wss://api.upbit.com/websocket/v1"
        self.markets = markets
        self.types = types
        self.ws = None
        self.callback = callback or self.default_callback

    def default_callback(self, data):
        # 데이터 시각 정보와 코인, 현재가 출력
        market_code = data.get('code')
        trade_price = data.get('trade_price')
        # trade_timestamp를 사용하거나, 없으면 timestamp를 사용
        data_timestamp = data.get('trade_timestamp', data.get('timestamp'))

        # 타임스탬프를 사람이 읽기 쉬운 형태로 변환 (선택 사항)
        if data_timestamp:
            # 밀리초를 초로 변환
            dt_object = datetime.fromtimestamp(data_timestamp / 1000)
            formatted_time = dt_object.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] # 밀리초까지 표시
            print(f"[🟢 실시간 데이터 수신] 시각: {formatted_time} | 코인: {market_code} | 가격: {trade_price}")
        else:
            print(f"[🟢 실시간 데이터 수신] 코인: {market_code} | 가격: {trade_price} (시각 정보 없음)")


    def _on_message(self, ws, message):
        data = json.loads(message)
        self.callback(data)

    def _on_error(self, ws, error):
        print("[ERROR]", error)

    def _on_close(self, ws, close_status_code, close_msg):
        print("[CLOSED]", close_status_code, close_msg)

    def _on_open(self, ws):
        print("[CONNECTED] Subscribing to:", self.markets)
        subscribe_data = [
            {"ticket": "test"},
            {
                "type": self.types[0],
                "codes": self.markets,
                "isOnlyRealtime": True,
            },
        ]
        ws.send(json.dumps(subscribe_data))

    def run_forever(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )

        thread = threading.Thread(target=self.ws.run_forever)
        thread.daemon = True
        thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[EXIT] WebSocket stopped manually.")
            self.ws.close()



###################### 기존 코드v1 #########################
# import websocket
# import json
# import threading
# import time

# class WebSocketManager:
#     def __init__(self, markets=["KRW-BTC"], types=["ticker"], callback=None):
#         self.url = "wss://api.upbit.com/websocket/v1"
#         self.markets = markets
#         self.types = types
#         self.ws = None
#         self.callback = callback or self.default_callback

#     def default_callback(self, data):
#         print("[DATA]", data)

#     def _on_message(self, ws, message):
#         data = json.loads(message)
#         self.callback(data)

#     def _on_error(self, ws, error):
#         print("[ERROR]", error)

#     def _on_close(self, ws, close_status_code, close_msg):
#         print("[CLOSED]", close_status_code, close_msg)

#     def _on_open(self, ws):
#         print("[CONNECTED] Subscribing to:", self.markets)
#         subscribe_data = [
#             {"ticket": "test"},
#             {
#                 "type": self.types[0],  # 예: "ticker", "trade", "orderbook"
#                 "codes": self.markets,
#                 "isOnlyRealtime": True,
#             },
#         ]
#         ws.send(json.dumps(subscribe_data))

#     def run_forever(self):
#         self.ws = websocket.WebSocketApp(
#             self.url,
#             on_message=self._on_message,
#             on_error=self._on_error,
#             on_close=self._on_close,
#             on_open=self._on_open
#         )

#         thread = threading.Thread(target=self.ws.run_forever)
#         thread.daemon = True
#         thread.start()

#         try:
#             while True:
#                 time.sleep(1)
#         except KeyboardInterrupt:
#             print("\n[EXIT] WebSocket stopped manually.")
#             self.ws.close()
