import requests
import jwt
import uuid
import hashlib
import os
import time

class UpbitAPI:
    def __init__(self, access_key: str, secret_key: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.server_url = "https://api.upbit.com"

    def _generate_token(self, payload: dict) -> dict:
        jwt_token = jwt.encode(payload, self.secret_key)
        authorize_token = f"Bearer {jwt_token}"
        headers = {"Authorization": authorize_token}
        return headers

    def get_markets(self) -> list:
        """전체 마켓 리스트 조회"""
        url = f"{self.server_url}/v1/market/all"
        response = requests.get(url)
        return response.json()

    def get_balance(self) -> list:
        """보유 자산 조회"""
        payload = {
            "access_key": self.access_key,
            "nonce": str(uuid.uuid4()),
        }
        headers = self._generate_token(payload)
        res = requests.get(f"{self.server_url}/v1/accounts", headers=headers)
        return res.json()

    def get_orderbook(self, markets: list) -> dict:
        """호가 정보 조회"""
        url = f"{self.server_url}/v1/orderbook"
        params = {"markets": ",".join(markets)}
        res = requests.get(url, params=params)
        return res.json()

    def place_order(self, market: str, side: str, volume: str, price: str, ord_type: str) -> dict:
        """주문 실행 (매수/매도)"""
        query = {
            'market': market,
            'side': side,
            'volume': volume,
            'price': price,
            'ord_type': ord_type,
        }
        query_string = "&".join([f"{key}={value}" for key, value in query.items()])
        m = hashlib.sha512()
        m.update(query_string.encode())
        query_hash = m.hexdigest()

        payload = {
            "access_key": self.access_key,
            "nonce": str(uuid.uuid4()),
            "query_hash": query_hash,
            "query_hash_alg": "SHA512",
        }

        headers = self._generate_token(payload)
        res = requests.post(f"{self.server_url}/v1/orders", params=query, headers=headers)
        return res.json()
