import requests

BASE_URL = "https://api.upbit.com/v1"

def get_candles(market: str, unit: int = 60, count: int = 100):
    """
    Upbit 분봉 캔들 가져오기
    :param market: 'KRW-BTC'
    :param unit: 분봉 단위 (1, 3, 5, 15, 30, 60, 240)
    :param count: 가져올 개수 (최대 200)
    """
    url = f"{BASE_URL}/candles/minutes/{unit}"
    params = {
        "market": market,
        "count": count
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print("⚠️ 캔들 데이터 요청 실패:", response.text)
        return []
