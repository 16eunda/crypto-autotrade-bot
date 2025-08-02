import sqlite3
import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
import time
from itertools import combinations, product

# ⏱️ 시작 시간
start_time = time.time()

# ✅ 설정
IsAllTicker = False
target_symbols = ["KRW-BTC"]


# ✅ DB 연결 설정
db_path = r"경로 설정 필요!\List.db"
table_name = "VolumeT"


# ✅ 지표별 단기/중기/장기 기간 설정
indicator_windows = {
    'SMA': [5, 14, 50],
    'EMA': [5, 14, 50],
    'RSI': [5, 14, 50],
    'BOLL': [10, 20, 60],
    'MACD': [(12, 26, 9)]
}


# ✅ 기술적 지표 계산
def calculate_indicators(df):
    for ind, windows in indicator_windows.items():
        if ind == 'MACD':
            for f, s, n in windows:
                macd = MACD(df['Price'], window_fast=f,
                            window_slow=s, window_sign=n)
                df[f'macd_{f}_{s}_{n}'] = macd.macd()
                df[f'macd_signal_{f}_{s}_{n}'] = macd.macd_signal()
        elif ind == 'BOLL':
            for w in windows:
                bb = BollingerBands(df['Price'], window=w)
                df[f'bb_upper_{w}'] = bb.bollinger_hband()
                df[f'bb_lower_{w}'] = bb.bollinger_lband()
        elif ind == 'SMA':
            for w in windows:
                df[f'SMA_{w}'] = SMAIndicator(
                    df['Price'], window=w).sma_indicator()
        elif ind == 'EMA':
            for w in windows:
                df[f'EMA_{w}'] = EMAIndicator(
                    df['Price'], window=w).ema_indicator()
        elif ind == 'RSI':
            for w in windows:
                df[f'RSI_{w}'] = RSIIndicator(df['Price'], window=w).rsi()
    return df


# ✅ 시그널 생성
def generate_signals(df, strategy_name):
    signal = np.zeros(len(df))

    if strategy_name.startswith("SMA_"):
        period = int(strategy_name.split("_")[1])
        sma = df[f"SMA_{period}"]
        buy = (df['Price'] > sma) & (df['Price'].shift() <= sma.shift())
        sell = (df['Price'] < sma) & (df['Price'].shift() >= sma.shift())
    elif strategy_name.startswith("EMA_"):
        period = int(strategy_name.split("_")[1])
        ema = df[f"EMA_{period}"]
        buy = (df['Price'] > ema) & (df['Price'].shift() <= ema.shift())
        sell = (df['Price'] < ema) & (df['Price'].shift() >= ema.shift())
    elif strategy_name.startswith("RSI_"):
        period = int(strategy_name.split("_")[1])
        rsi = df[f"RSI_{period}"]
        buy = rsi < 45
        sell = rsi > 55
    elif strategy_name.startswith("BOLL_"):
        period = int(strategy_name.split("_")[1])
        buy = df['Price'] < df[f'bb_lower_{period}']
        sell = df['Price'] > df[f'bb_upper_{period}']
    elif strategy_name.startswith("MACD_"):
        _, f, s, n = strategy_name.split("_")
        f, s, n = int(f), int(s), int(n)
        macd = df[f'macd_{f}_{s}_{n}']
        macd_signal = df[f'macd_signal_{f}_{s}_{n}']
        buy = (macd > macd_signal) & (macd.shift() <= macd_signal.shift())
        sell = (macd < macd_signal) & (macd.shift() >= macd_signal.shift())
    else:
        return pd.Series(signal, index=df.index)

    signal[buy.fillna(False)] = 1
    signal[sell.fillna(False)] = -1
    return pd.Series(signal, index=df.index)


# ✅ 시그널 조합
def generate_combined_signals(df, strategies):
    signals = [generate_signals(df, s) for s in strategies]
    signal_df = pd.concat(signals, axis=1)
    buy = (signal_df == 1).all(axis=1)
    sell = (signal_df == -1).all(axis=1)
    combined = pd.Series(0, index=df.index)
    combined[buy] = 1
    combined[sell] = -1
    return combined


def generate_combined_signals_or(df, strategies):
    signals = [generate_signals(df, s) for s in strategies]
    signal_df = pd.concat(signals, axis=1)
    buy = (signal_df == 1).any(axis=1)
    sell = (signal_df == -1).any(axis=1)
    combined = pd.Series(0, index=df.index)
    combined[buy] = 1
    combined[sell] = -1
    return combined


def generate_weighted_signal(df, strategies):
    score = pd.Series(0, index=df.index, dtype=float)
    for strat in strategies:
        score += generate_signals(df, strat)
    avg = score / len(strategies)
    signal = pd.Series(0, index=df.index)
    signal[avg >= 0.5] = 1
    signal[avg <= -0.5] = -1
    return signal


# ✅ 거래 시뮬레이션
def simulate_trading_fast(df, signal, initial_cash=100000):
    cash = initial_cash
    holding = 0.0
    history = []
    position_open = False

    for i in range(len(df)):
        price = df['Price'].iloc[i]

        # 매수 조건: 신호가 1이고, 현금이 있고, 보유하지 않은 경우만 매수
        if signal.iloc[i] == 1 and cash > 0 and not position_open:
            holding = cash / price
            cash = 0
            position_open = True
            history.append((df.index[i], 'BUY', price))

        # 매도 조건: 신호가 -1이고, 보유 중일 때만 매도
        elif signal.iloc[i] == -1 and position_open:
            cash = holding * price
            holding = 0
            position_open = False
            history.append((df.index[i], 'SELL', price))

    # 최종 자산 계산
    final_value = cash + holding * df['Price'].iloc[-1]
    return_rate = (final_value - initial_cash) / initial_cash * 100
    total_profit = final_value - initial_cash
    return return_rate, history, total_profit


# ✅ 전략 키 생성
def get_all_strategy_keys():
    all_keys = {}
    for ind, windows in indicator_windows.items():
        if ind == 'MACD':
            all_keys[ind] = [f"MACD_{f}_{s}_{n}" for (f, s, n) in windows]
        else:
            all_keys[ind] = [f"{ind}_{w}" for w in windows]
    return all_keys

# ✅ 분석 함수
def analyze_symbol(symbol):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql(f"""
        SELECT CurrentTime, Price FROM {table_name}
        WHERE TickerName = '{symbol}' ORDER BY CurrentTime ASC
    """, conn)
    conn.close()

    if df.empty:
        return symbol, None, None, [], []

    df['CurrentTime'] = pd.to_datetime(df['CurrentTime'])
    df.set_index('CurrentTime', inplace=True)
    df['Price'] = df['Price'].astype(float)
    df = df[~df.index.duplicated()]
    df = calculate_indicators(df)

    base_strategies = ['SMA', 'EMA', 'RSI', 'BOLL', 'MACD']
    all_keys = get_all_strategy_keys()

    results = {}

    # 단일 전략
    for strat in base_strategies:
        for strategy_name in all_keys[strat]:
            sig = generate_signals(df, strategy_name)
            # ret, trades = simulate_trading_fast(df, sig)
            # results[strategy_name] = {'return': ret, 'trades': trades}
            ret, trades, profit = simulate_trading_fast(df, sig)
            results[strategy_name] = {'return': ret,
                                      'trades': trades, 'profit': profit}

    # 복합 전략
    for r in [2, 3, 4]:
        for combo in combinations(base_strategies, r):
            name = "+".join(combo)
            strat_combos = list(product(*[all_keys[c] for c in combo]))
            for sc in strat_combos:
                sc_name = "+".join(sc)

                # sig_and = generate_combined_signals(df, sc)
                # ret_and, trades_and = simulate_trading_fast(df, sig_and)
                # results[sc_name] = {'return': ret_and, 'trades': trades_and}

                # sig_or = generate_combined_signals_or(df, sc)
                # ret_or, trades_or = simulate_trading_fast(df, sig_or)
                # results[f"{sc_name} [OR]"] = {
                #     'return': ret_or, 'trades': trades_or}

                # sig_wt = generate_weighted_signal(df, sc)
                # ret_wt, trades_wt = simulate_trading_fast(df, sig_wt)
                # results[f"{sc_name} [WEIGHTED]"] = {
                #     'return': ret_wt, 'trades': trades_wt}

                sig_and = generate_combined_signals(df, sc)
                ret_and, trades_and, profit_and = simulate_trading_fast(
                    df, sig_and)
                results[sc_name] = {'return': ret_and,
                                    'trades': trades_and, 'profit': profit_and}

                sig_or = generate_combined_signals_or(df, sc)
                ret_or, trades_or, profit_or = simulate_trading_fast(
                    df, sig_or)
                results[f"{sc_name} [OR]"] = {'return': ret_or,
                                              'trades': trades_or, 'profit': profit_or}

                sig_wt = generate_weighted_signal(df, sc)
                ret_wt, trades_wt, profit_wt = simulate_trading_fast(
                    df, sig_wt)
                results[f"{sc_name} [WEIGHTED]"] = {
                    'return': ret_wt, 'trades': trades_wt, 'profit': profit_wt}

    sorted_results = sorted(
        results.items(), key=lambda x: x[1]['return'], reverse=True)
    best_name, best_result = sorted_results[0]
    return symbol, best_name, best_result['return'], best_result['trades'], sorted_results


# ✅ 실행
if IsAllTicker:
    conn = sqlite3.connect(db_path)
    tickers = pd.read_sql(f"SELECT DISTINCT TickerName FROM {
                          table_name}", conn)['TickerName'].tolist()
    conn.close()

    for symbol in tickers:
        name, strategy, ret, _, sorted_results = analyze_symbol(symbol)
        if strategy:
            print(f"\n📈 종목명: {name}")
            print(f"🏆 최고 전략: {strategy}")
            print(f"💰 수익률: {ret:.2f}%")
            print("\n📊 전략별 수익률:")

            rank = 50  # 상위 순위 기준 출력(%)
            # for strat_name, result in sorted_results[:rank]:
            #     print(f"{strat_name:<50} ➤ 수익률: {result['return']:.2f}%")
            for strat_name, result in sorted_results[:rank]:
                print(f"{strat_name:<50} ➤ 수익률: {
                      result['return']:.2f}% | 수익금: {result['profit']:.2f}원")

            # threshold = 20.0  # 수익률 기준 출력(%)
            # for strat_name, result in sorted_results:
            #     if result['return'] >= threshold:
            #         print(f"{strat_name:<50} ➤ 수익률: {result['return']:.2f}%")

else:
    for symbol in target_symbols:
        name, strategy, ret, trades, sorted_results = analyze_symbol(symbol)
        if strategy:
            print(f"\n📈 종목명: {name}")
            print(f"🏆 최고 전략: {strategy}")
            print(f"💰 수익률: {ret:.2f}%")
            print("\n📊 전략별 수익률:")

            rank = 50  # 상위 순위 기준 출력(%)
            # for strat_name, result in sorted_results[:rank]:
            #     print(f"{strat_name:<50} ➤ 수익률: {result['return']:.2f}%")
            for strat_name, result in sorted_results[:rank]:
                print(f"{strat_name:<50} ➤ 수익률: {
                      result['return']:.2f}% | 수익금: {result['profit']:.2f}원")

            # threshold = 20.0  # 수익률 기준 출력(%)
            # for strat_name, result in sorted_results:
            #     if result['return'] >= threshold:
            #         print(f"{strat_name:<50} ➤ 수익률: {result['return']:.2f}%")

# ⏱️ 종료 시간
end_time = time.time()
print(f"\n⏱️ 테스트 소요 시간: {end_time - start_time:.2f}초")
