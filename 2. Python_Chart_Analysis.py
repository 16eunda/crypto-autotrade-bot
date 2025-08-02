import pdb
import sqlite3
from datetime import datetime
import numpy as np
import pandas as pd

# Tkinter 윈도우 속성 설정을 위한 import
# pip install tkinter
# pip install matplotlib
import tkinter as tk
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# 미사용
import time
import os
import sys



# 테스트 방법 
# 1. 실행 후 오류가 발생하는 필요 패키지 전부 다운로드 (pip install ...)
# 2. Git에 List.db 로컬에 다운로드 후 원하는 경로에 넣기
# 3. conn = sqlite3.connect('경로 수정\\List.db')에 List.db 경로 넣기
# 4. ★★★★★★★★★★ 표시가 있는 곳에서 이동평균, 볼린저밴드 범위, 급등/급락 조건을 수정하여 최적의 매수/매도 타이밍 찾기
# 5. 추가 오류나 궁금한 부분은 슬랙 채널로 질문 올려주세요!


GV_TICKER_NAME = 'KRW-BTC' # Chat 분석 종목 설정


# SQLite DB 연결
conn = sqlite3.connect('경로 수정\\List.db')
cursor = conn.cursor()

# 데이터 가져오기
cursor.execute("""
    SELECT CurrentTime, Price, Volume FROM VolumeT 
    WHERE TickerName = ? 
    ORDER BY CurrentTime ASC
""", (GV_TICKER_NAME,))

rows = cursor.fetchall()
conn.close()

# 날짜 파싱
timestamps = [datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S') for row in rows]
prices = [row[1] for row in rows]
volumes = [row[2] for row in rows]

# numpy 배열로 변환
prices_np = np.array(prices)

# 이동평균 계산
ma_short = np.convolve(prices_np, np.ones(24)/24, mode='valid')  # 24일선
ma_long = np.convolve(prices_np, np.ones(48)/48, mode='valid')   # 48일선

# 볼린저밴드 계산 (20일 기준)
window = 20
rolling_mean = np.convolve(prices_np, np.ones(window)/window, mode='valid')
rolling_std = np.array([
	np.std(prices_np[i-window:i]) if i >= window else np.nan
	for i in range(len(prices_np))
])
bollinger_upper = rolling_mean + 2 * rolling_std[window-1:]
bollinger_lower = rolling_mean - 2 * rolling_std[window-1:]
bb_timestamps = timestamps[window-1:]



# 이동평균/볼린저밴드 계산 시 오프셋 ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
ma_offset_24 = 23
ma_offset_48 = 47
bb_offset = 19

# 급등/급락 포인트 저장 리스트
spike_indices = []
drop_indices = []

avg_bb_width = np.nanmean(bollinger_upper - bollinger_lower)

# Pandas로 Series 생성
price_series = pd.Series(prices_np)
volume_series = pd.Series(volumes)

# EMA 계산
ema_12 = price_series.ewm(span=12).mean()
ema_26 = price_series.ewm(span=26).mean()
macd = ema_12 - ema_26
macd_signal = macd.ewm(span=9).mean()

# 거래량 평균 (20개 기준)
# 거래량 평균 (20개 기준)
rolling_volume_mean = volume_series.rolling(window=20).mean()

for i in range(48, len(prices_np) - 10):  # 충분한 과거 데이터 확보
	# 이동평균선
	short_ma = ma_short[i - ma_offset_24]
	long_ma = ma_long[i - ma_offset_48]

	# 볼린저밴드 폭
	bb_i = i - bb_offset
	if bb_i < 0 or bb_i >= len(bollinger_upper):
		continue
	bb_width = bollinger_upper[bb_i] - bollinger_lower[bb_i]

	# EMA, MACD
	if i >= len(macd) or i >= len(macd_signal):
		continue
	ema_cond = ema_12[i] > ema_26[i]
	macd_cond = macd[i] > macd_signal[i]
	
	# ? 거래량 조건
#	volume_cond = volumes[i] > rolling_volume_mean[i] * 1.5 if not np.isnan(rolling_volume_mean[i]) else False
	volume_cond = volumes[i] > rolling_volume_mean[i] * 1.2 if not np.isnan(rolling_volume_mean[i]) else False


#급등/급락 조건 확인 시 미래 데이터를 사용하면 안 됨!실시간 확인이 불가능!!
# 최소 20개 이전 데이터가 있어야 비교 가능
	if i < 68:
	    continue

	# 급등 조건	★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
	# 과거 구간 추출
	past =5 # 과거 6개 구간 추출
	ma_short_past = ma_short[i - ma_offset_24 - past : i - ma_offset_24 + 1]
	ma_long_past = ma_long[i - ma_offset_48 - past : i - ma_offset_48 + 1]
	bb_upper_past = bollinger_upper[i - bb_offset - past : i - bb_offset + 1]
	bb_lower_past = bollinger_lower[i - bb_offset - past : i - bb_offset + 1]
	price_past = prices_np[i - past : i + 1]

	# 조건 1: MA Short < MA Long (전부)
	ma_compare = np.all(ma_short_past < ma_long_past)

	# 조건 2: MA 차이 줄어듦 (수렴)
	ma_diff = ma_long_past - ma_short_past
	ma_diff_slope = np.polyfit(range(len(ma_diff)), ma_diff, 1)[0]
	ma_converging = ma_diff_slope < 0

	# 조건 3: 볼린저밴드 폭 넓어지는 중
	bb_width_past = bb_upper_past - bb_lower_past
	bb_width_slope = np.polyfit(range(len(bb_width_past)), bb_width_past, 1)[0]
	bb_expanding = bb_width_slope > 0  # 폭이 넓어지는 추세

	# 조건 4: 가격과 MA들이 모두 상승 전환 중 (기울기 양수)
	price_slope = np.polyfit(range(len(price_past)), price_past, 1)[0]
	ma_short_slope = np.polyfit(range(len(ma_short_past)), ma_short_past, 1)[0]
	ma_long_slope = np.polyfit(range(len(ma_long_past)), ma_long_past, 1)[0]
	all_upward = price_slope > 0 and ma_short_slope > 0 and ma_long_slope > 0

	# 최종 조건
	if ma_compare and ma_converging and bb_expanding and all_upward:
#	if ma_compare and ma_converging and bb_expanding and all_upward and volume_cond: 
		spike_indices.append(i)



	# 최소 20개 이전 데이터가 있어야 비교 가능
	if i < 68:
	    continue

	# 급락 조건	★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
	# 과거 20개 구간 추출
	past = 5 # 과거 20개 구간 추출
	ma_short_past = ma_short[i - ma_offset_24 - past : i - ma_offset_24 + 1]
	ma_long_past = ma_long[i - ma_offset_48 - past : i - ma_offset_48 + 1]
	bb_upper_past = bollinger_upper[i - bb_offset - past : i - bb_offset + 1]
	bb_lower_past = bollinger_lower[i - bb_offset - past : i - bb_offset + 1]
	price_past = prices_np[i - past : i + 1]

	# 조건 1: MA Short > MA Long (전부)
	ma_compare = np.all(ma_short_past > ma_long_past)

	# 조건 2: MA 차이 줄어듦
	ma_diff = ma_short_past - ma_long_past
	ma_diff_slope = np.polyfit(range(len(ma_diff)), ma_diff, 1)[0]  # 기울기
	ma_converging = ma_diff_slope < 0  # 차이가 줄어들고 있어야 함

	# 조건 3: 볼린저밴드 폭 줄어듦
	bb_width_past = bb_upper_past - bb_lower_past
	bb_width_slope = np.polyfit(range(len(bb_width_past)), bb_width_past, 1)[0]
	bb_converging = bb_width_slope < 0  # 폭이 줄어드는 추세

	# 조건 4: 가격/MA 모두 상승 중
	price_slope = np.polyfit(range(len(price_past)), price_past, 1)[0]
	ma_short_slope = np.polyfit(range(len(ma_short_past)), ma_short_past, 1)[0]
	ma_long_slope = np.polyfit(range(len(ma_long_past)), ma_long_past, 1)[0]
	all_upward = price_slope > 0 and ma_short_slope > 0 and ma_long_slope > 0

	# 최종 조건
	if ma_compare and ma_converging and bb_converging and all_upward:
#	if ma_compare and ma_converging and bb_converging and all_upward and volume_cond: 
		drop_indices.append(i)






# Tkinter 윈도우 생성
root = tk.Tk()
root.title("KRW-BTC Chart")

# matplotlib Figure 생성
#fig, ax1 = plt.subplots(figsize=(12, 6))
fig = Figure(figsize=(12, 6), dpi=100)
ax1 = fig.add_subplot(111)

# 가격선 및 이동평균, 볼린저밴드
ax1.set_xlabel('Time')
ax1.set_ylabel('Price (KRW)', color='green') 
ax1.plot(timestamps, prices, color='green', label='Price') # 가격 (초록색)
ax1.plot(timestamps[23:], ma_short, color='red', label='MA 24') # 이동평균 Short (빨간색)
ax1.plot(timestamps[47:], ma_long, color='blue', label='MA 48') # 이동평균 Long (파란색)
ax1.plot(bb_timestamps, bollinger_upper, color='grey', linestyle='-', label='Bollinger Upper') # 볼린저밴드 상단
ax1.plot(bb_timestamps, bollinger_lower, color='grey', linestyle='-', label='Bollinger Lower') # 볼린저밴드 하단
ax1.tick_params(axis='y', labelcolor='green')

	
			
# 빨간색 급등 세로선
for idx in spike_indices:
	ax1.axvline(x=timestamps[idx], color='red', alpha=0.5, linestyle='-', linewidth=1.2)

# 파란색 급락 세로선
for idx in drop_indices:
	ax1.axvline(x=timestamps[idx], color='blue', alpha=0.5, linestyle='-', linewidth=1.2)




# # 거래량
ax2 = ax1.twinx()
ax2.set_ylabel('Volume', color='purple')
#ax2.plot(timestamps, volumes, color='orange', label='Volume')
ax2.plot(timestamps, volumes, color='purple', alpha=0.3, label='Volume')
ax2.tick_params(axis='y', labelcolor='purple')

# 시간 포맷
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

# # 시간 포맷 설정 → 일자 단위로 변경
# ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
# ax1.xaxis.set_major_locator(mdates.DayLocator())
# fig.autofmt_xdate(rotation=45)

# 범례
ax1.legend(loc='upper left')

plt.title("KRW-BTC Price, Volume, MA, and Bollinger Bands")
plt.grid(True)
plt.tight_layout()

# Figure를 Tkinter 윈도우에 삽입
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


# 차트 저장(필요 시)
# image_path = f"저장 경로 수정\\Python_{GV_TICKER_NAME}.png"
# fig.savefig(image_path, dpi=300)
# print(f"차트를 저장했습니다: {image_path}")
# sys.exit()



# Navigation Toolbar (줌/확대/저장)
toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()
toolbar.pack(side=tk.TOP, fill=tk.X)



# 창 실행
root.mainloop()




