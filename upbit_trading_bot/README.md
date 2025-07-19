# Upbit Trading Bot

업비트 실시간 데이터 수신 및 자동 매매를 위한 파이썬 봇 프로젝트입니다.

## 폴더 구조

```
upbit_trading_bot/
├── main.py                # 진입점(main 함수)
├── pyproject.toml         # 프로젝트 및 의존성 관리
├── .env                   # API 키 등 환경 변수 파일
├── services/
│   ├── upbit_api.py       # 업비트 REST API 래퍼
│   └── websocket.py       # 업비트 웹소켓 실시간 데이터 수신
├── tests/
│   ├── test_api.py        # REST API 기능 테스트
│   └── test_websocket.py  # 웹소켓 기능 테스트
```

## 주요 기능

- **REST API 연동**  
  [`UpbitAPI`](services/upbit_api.py) 클래스를 통해 마켓 조회, 잔고 조회, 호가 정보, 주문 기능 제공

- **실시간 데이터 수신**  
  [`WebSocketManager`](services/websocket.py) 클래스를 통해 실시간 시세, 거래 정보 수신 및 콜백 처리

- **테스트 코드**  
  [`test_api.py`](tests/test_api.py), [`test_websocket.py`](tests/test_websocket.py)에서 주요 기능 동작 확인

## 설치 및 실행

1. 의존성 설치 (생략 가능, uv run 할 때 자동 설치됨)  
   ```sh
   uv add dotenv requests PyJWT websocket-client
   ```

2. 환경 변수 설정  
   `.env` 파일에 아래와 같이 업비트 API 키를 입력
   ```
   UPBIT_ACCESS_KEY=your_access_key
   UPBIT_SECRET_KEY=your_secret_key
   ```

3. 테스트 실행  
   ```sh
   uv run -m tests.test_api
   uv run -m tests.test_websocket  
   ```

4. 메인 실행  
   ```sh
   uv run main.py
   ```

## 참고

- 업비트 공식 API 문서: https://docs.upbit.com/
- 실시간 데이터는 웹소켓을 통해 수신하며, 콜백 함수에서 원하는 방식으로 처리 가능

---
문의 및 개선 제안은 이슈로 남겨주세요.