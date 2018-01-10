# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017 reverendus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import urllib
import hashlib

import requests

from pymaker import Wad


class OKCoinApi:
    """OKCoin and OKEX API interface.

    Developed according to the following manual:
    <https://www.okex.com/intro_apiOverview.html>.

    Inspired by the following example:
    <https://github.com/OKCoin/rest>, <https://github.com/OKCoin/rest/tree/master/python>.
    """

    def __init__(self, api_server: str, api_key: str, secret_key: str, timeout: float):
        assert(isinstance(api_server, str))
        assert(isinstance(api_key, str))
        assert(isinstance(secret_key, str))
        assert(isinstance(timeout, float))

        self.api_server = api_server
        self.api_key = api_key
        self.secret_key = secret_key
        self.timeout = timeout

    def ticker(self, symbol: str):
        return self._http_get("/api/v1/ticker.do", f"symbol={symbol}")

    def depth(self, symbol: str):
        return self._http_get("/api/v1/depth.do", f"symbol={symbol}")

    def trades(self, symbol: str):
        return self._http_get("/api/v1/trades.do", f"symbol={symbol}")
    
    def user_info(self):
        return self._http_post("/api/v1/userinfo.do", {})

    def place_order(self, symbol: str, is_sell: bool, price: Wad, amount: Wad) -> int:
        assert(isinstance(symbol, str))
        assert(isinstance(is_sell, bool))
        assert(isinstance(price, Wad))
        assert(isinstance(amount, Wad))

        result = self._http_post("/api/v1/trade.do", {
            'symbol': symbol,
            'type': 'sell' if is_sell else 'buy',
            'price': float(price),
            'amount': float(amount)
        })

        return int(result['order_id'])

    def batch_place_order(self, symbol, trade_type, orders_data):
        params = {
            'symbol': symbol,
            'type': trade_type,
            'orders_data': orders_data
        }
        return self._http_post("/api/v1/batch_trade.do", params)

    def cancel_order(self, symbol: str, order_id: int) -> bool:
        assert(isinstance(symbol, str))
        assert(isinstance(order_id, int))

        result = self._http_post("/api/v1/cancel_order.do", {
            'symbol': symbol,
            'order_id': order_id
        })

        return int(result['order_id']) == order_id

    def orderinfo(self, symbol, order_id):
        params = {
         'symbol': symbol,
         'order_id': order_id
        }
        return self._http_post("/api/v1/order_info.do", params)

    def ordersinfo(self, symbol, order_id, trade_type):
        params = {
         'symbol': symbol,
         'order_id': order_id,
         'type': trade_type
        }
        return self._http_post("/api/v1/orders_info.do", params)

    def order_history(self, symbol, status, current_page, page_length):
        params = {
          'symbol': symbol,
          'status': status,
          'current_page': current_page,
          'page_length': page_length
        }
        return self._http_post("/api/v1/order_history.do", params)

    def _create_signature(self, params: dict):
        assert(isinstance(params, dict))

        sign = ''
        for key in sorted(params.keys()):
            sign += key + '=' + str(params[key]) + '&'
        data = sign + 'secret_key=' + self.secret_key
        return hashlib.md5(data.encode("utf8")).hexdigest().upper()

    @staticmethod
    def _result(result) -> dict:
        data = result.json()

        if 'error_code' in data:
            raise Exception(f"OKCoin API error: {data['error_code']}")

        if 'result' not in data or data['result'] is not True:
            raise Exception(f"Negative OKCoin response: {data}")

        return data

    def _http_get(self, resource: str, params: str):
        assert(isinstance(resource, str))
        assert(isinstance(params, str))

        return self._result(requests.get(url=f"https://{self.api_server}{resource}?{params}",
                                         timeout=self.timeout))

    def _http_post(self, resource: str, params: dict):
        assert(isinstance(resource, str))
        assert(isinstance(params, dict))

        params['api_key'] = self.api_key
        params['sign'] = self._create_signature(params)

        return self._result(requests.post(url=f"https://{self.api_server}{resource}",
                                          data=urllib.parse.urlencode(params),
                                          headers={"Content-Type": "application/x-www-form-urlencoded"},
                                          timeout=self.timeout))
