from strategies.candle_rsi import CandleRSIStrategy

if __name__ == "__main__":
    # 1시간봉 RSI 전략 테스트
    strategy = CandleRSIStrategy(market="KRW-BTC", unit=60)

    print("📡 캔들 데이터 요청 중...")
    rsi = strategy.fetch_rsi()

    print("📊 RSI 결과:", rsi)

    if rsi is None:
        print("⚠️ RSI 계산 실패 (데이터를 가져오지 못했을 가능성)")
    else:
        if strategy.should_buy():
            print("🟢 매수 신호")
        elif strategy.should_sell():
            print("🔴 매도 신호")
        else:
            print("⏸️ 관망")
