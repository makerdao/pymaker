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

import http.client
import urllib
import json
import hashlib

import requests


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

    def place_order(self, symbol, trade_type, price='', amount=''):
        params = {
            'symbol': symbol,
            'type': trade_type
        }
        if price:
            params['price'] = price
        if amount:
            params['amount'] = amount

        return self._http_post("/api/v1/trade.do", params)

    def batch_place_order(self, symbol, trade_type, orders_data):
        params = {
            'symbol': symbol,
            'type': trade_type,
            'orders_data': orders_data
        }
        return self._http_post("/api/v1/batch_trade.do", params)

    def cancel_order(self, symbol, order_id):
        params = {
             'symbol': symbol,
             'order_id': order_id
        }
        return self._http_post("/api/v1/cancel_order.do", params)

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

    def _create_signature(self, params):
        sign = ''
        for key in sorted(params.keys()):
            sign += key + '=' + str(params[key]) + '&'
        data = sign + 'secret_key=' + self.secret_key
        return hashlib.md5(data.encode("utf8")).hexdigest().upper()

    def _http_get(self, resource: str, params: str):
        assert(isinstance(resource, str))
        assert(isinstance(params, str))

        result = requests.get(f"https://{self.api_server}{resource}?{params}", timeout=self.timeout)
        return result.json()

    def _http_post(self, resource: str, params: dict):
        assert(isinstance(resource, str))
        assert(isinstance(params, dict))

        headers = {
            "Content-type": "application/x-www-form-urlencoded",
        }
        conn = http.client.HTTPSConnection(self.api_server, timeout=self.timeout)
        params['api_key'] = self.api_key
        params['sign'] = self._create_signature(params)
        temp_params = urllib.parse.urlencode(params)
        conn.request("POST", resource, temp_params, headers)
        response = conn.getresponse()
        data = response.read().decode('utf-8')
        params.clear()
        conn.close()
        return data
