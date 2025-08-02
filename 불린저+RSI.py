import pyupbit, time, requests, sqlite3
from datetime import datetime

# ────────── 설정 ──────────
ACCESS = "your-access-key"
SECRET = "your-secret-key"
TELEGRAM_TOKEN = "your-telegram-token"
TELEGRAM_CHAT_ID = "your-chat-id"
DB_PATH = "bollinger_trades_safe.db"

FEE_RATE = 0.0005
ORDER_KRW = 10_000.0
ORDER_TOTAL = ORDER_KRW * (1 + FEE_RATE)  # = 10,005원
PROFIT_THRESHOLD = 3.0  # 최소 수익률 2%

TICKERS = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-MATIC"]
upbit = pyupbit.Upbit(ACCESS, SECRET)

# ────────── 텔레그램 알림 ──────────
def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

# ────────── DB 초기화 및 기록 ──────────
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                ticker TEXT,
                volume REAL,
                price REAL,
                profit REAL,
                return_rate REAL,
                date TEXT
            )
        """)
        conn.commit()

def log_trade(action, ticker, volume, price, profit=None, return_rate=None):
    today = datetime.now().strftime('%Y-%m-%d')
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""INSERT INTO trades (action, ticker, volume, price, profit, return_rate, date)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (action, ticker, volume, price, profit, return_rate, today))
        conn.commit()

def already_bought_today(ticker):
    today = datetime.now().strftime('%Y-%m-%d')
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""SELECT 1 FROM trades 
                     WHERE action = 'BUY' AND ticker = ? AND date = ?""",
                  (ticker, today))
        return c.fetchone() is not None

# ────────── 지표 계산 ──────────
def get_bollinger(df, window=20, std=2):
    df["ma"] = df["close"].rolling(window).mean()
    df["std"] = df["close"].rolling(window).std()
    df["upper"] = df["ma"] + (std * df["std"])
    df["lower"] = df["ma"] - (std * df["std"])
    return df

def get_rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))
    return df

# ────────── 조건 판별 ──────────
def check_buy(df):
    df = get_bollinger(df)
    df = get_rsi(df)

    # 볼린저 밴드 하단 이탈 후 재진입
    #RSI ≤ 30 -> 과매도
    return (
        df["close"].iloc[-2] < df["lower"].iloc[-2] and
        df["close"].iloc[-1] > df["lower"].iloc[-1] and
        df["rsi"].iloc[-1] <= 30
    )

def check_sell(df, buy_price):
    df = get_bollinger(df)
    current_price = df["close"].iloc[-1]
    ma = df["ma"].iloc[-1]
    return current_price > ma and ((current_price - buy_price) / buy_price * 100) >= PROFIT_THRESHOLD

# ────────── 매수 ──────────
def buy(ticker):
    krw_balance = float(upbit.get_balance("KRW"))
    if krw_balance < ORDER_TOTAL:
        print(f"[SKIP] {ticker} - 잔액 부족 (현재 KRW: {krw_balance:.0f})")
        return

    price = pyupbit.get_current_price(ticker)
    amount = (ORDER_KRW * (1 - FEE_RATE)) / price
    upbit.buy_market_order(ticker, ORDER_KRW)
    log_trade("BUY", ticker, amount, price)
    send_telegram(f"[매수] {ticker} {amount:.4f}개 @ {price:,.0f} KRW")

# ────────── 매도 ──────────
def sell(ticker):
    symbol = ticker.replace("KRW-", "")
    amount = upbit.get_balance(symbol)
    price = pyupbit.get_current_price(ticker)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""SELECT price, volume FROM trades 
                     WHERE ticker = ? AND action = 'BUY' ORDER BY id DESC LIMIT 1""", (ticker,))
        result = c.fetchone()

    if result:
        buy_price, volume = result
        df = pyupbit.get_ohlcv(ticker, interval="day", count=21)
        if check_sell(df, float(buy_price)):
            revenue = price * float(volume) * (1 - FEE_RATE)
            cost = float(buy_price) * float(volume)
            profit = revenue - cost
            return_rate = (profit / cost) * 100
            upbit.sell_market_order(ticker, amount)
            log_trade("SELL", ticker, float(volume), price, profit, return_rate)
            send_telegram(f"[매도] {ticker} {float(volume):.4f}개 @ {price:,.0f} KRW | 수익: {profit:,.0f}원 ({return_rate:.2f}%)")
        else:
            print(f"[보유중] {ticker} → 수익률/중심선 조건 미충족")
    else:
        send_telegram(f"[매도 실패] {ticker} - 매수 정보 없음")

# ────────── 실행 루프 ──────────
init_db()
round_no = 1

while True:
    try:
        print(f"\n[Round {round_no}] 실행 중...")
        round_no += 1
        balances = upbit.get_balances()
        holding = {b['currency']: float(b['balance']) for b in balances if b['currency'] != 'KRW'}

        for ticker in TICKERS:
            df = pyupbit.get_ohlcv(ticker, interval="day", count=21)
            if df is None or len(df) < 21:
                continue

            symbol = ticker.replace("KRW-", "")

            if symbol in holding and holding[symbol] > 0:
                sell(ticker)
            elif not already_bought_today(ticker) and check_buy(df):
                buy(ticker)
            else:
                print(f"[관망중] {ticker} → 조건 미충족 또는 이미 매수함")

        time.sleep(300)  # 5분 간격

    except Exception as e:
        print("에러 발생:", e)
        send_telegram(f"[에러 발생] {e}")
        time.sleep(30)
