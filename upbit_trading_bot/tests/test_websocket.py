from services.websocket import WebSocketManager
import datetime # datetime 모듈 추가

def custom_callback(data):
    # Upbit 웹소켓 데이터에서 타임스탬프 정보 추출
    # 'trade_timestamp'는 거래 발생 시각, 'timestamp'는 업비트 서버 수신 시각
    data_timestamp = data.get('trade_timestamp', data.get('timestamp'))

    if data_timestamp:
        # 밀리초 단위 타임스탬프를 초 단위로 변환 후 datetime 객체로 변환
        dt_object = datetime.datetime.fromtimestamp(data_timestamp / 1000)
        # 사람이 읽기 쉬운 형식으로 포맷팅 (밀리초까지 표시)
        formatted_time = dt_object.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        print(f"[🟢 실시간 데이터 수신] 시각: {formatted_time} | 코인: {data['code']} | 가격: {data['trade_price']}")
    else:
        # 타임스탬프 정보가 없을 경우 (드물지만 대비)
        print(f"[🟢 실시간 데이터 수신] 코인: {data['code']} | 가격: {data['trade_price']} (시각 정보 없음)")


if __name__ == "__main__":
    ws = WebSocketManager(
        markets=["KRW-BTC", "KRW-ETH"],
        types=["ticker"],
        callback=custom_callback # 여기에서 custom_callback을 사용하도록 되어 있음
    )
    ws.run_forever()


#################### 기존 코드v1 ################
# from upbit_trading_bot.services.websocket import WebSocketManager

# def custom_callback(data):
#     print("[🟢 실시간 데이터 수신]:", data["code"], data["trade_price"])

# if __name__ == "__main__":
#     ws = WebSocketManager(
#         markets=["KRW-BTC", "KRW-ETH"],
#         types=["ticker"],
#         callback=custom_callback
#     )
#     ws.run_forever()
