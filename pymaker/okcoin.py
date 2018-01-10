# -*- coding: utf-8 -*-

import http.client
import urllib
import json
import hashlib


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

    #Get OKCOIN spot market information
    def ticker(self, symbol):
        TICKER_RESOURCE = "/api/v1/ticker.do"
        params=''
        if symbol:
            params = 'symbol=%(symbol)s' %{'symbol':symbol}
        return self._http_get(TICKER_RESOURCE, params)

    #Obtain OKCOIN spot market depth information
    def depth(self, symbol):
        DEPTH_RESOURCE = "/api/v1/depth.do"
        params=''
        if symbol:
            params = 'symbol=%(symbol)s' %{'symbol':symbol}
        return self._http_get(DEPTH_RESOURCE, params)

    #Obtain OKCOIN spot historical transaction information
    def trades(self, symbol):
        TRADES_RESOURCE = "/api/v1/trades.do"
        params=''
        if symbol:
            params = 'symbol=%(symbol)s' %{'symbol':symbol}
        return self._http_get(TRADES_RESOURCE, params)
    
    #Get customer cash account information
    def userinfo(self):
        USERINFO_RESOURCE = "/api/v1/userinfo.do"
        params ={}
        params['api_key'] = self.api_key
        params['sign'] = self._build_my_sign(params)
        return self._http_post(USERINFO_RESOURCE, params)

    #Spot Trading
    def trade(self, symbol, tradeType, price='', amount=''):
        TRADE_RESOURCE = "/api/v1/trade.do"
        params = {
            'api_key':self.api_key,
            'symbol':symbol,
            'type':tradeType
        }
        if price:
            params['price'] = price
        if amount:
            params['amount'] = amount
            
        params['sign'] = self._build_my_sign(params)
        return self._http_post(TRADE_RESOURCE, params)

    #Spot bulk orders
    def batchTrade(self, symbol, tradeType, orders_data):
        BATCH_TRADE_RESOURCE = "/api/v1/batch_trade.do"
        params = {
            'api_key':self.api_key,
            'symbol':symbol,
            'type':tradeType,
            'orders_data':orders_data
        }
        params['sign'] = self._build_my_sign(params)
        return self._http_post(BATCH_TRADE_RESOURCE, params)

    #Spot cancel the order
    def cancelOrder(self, symbol, orderId):
        CANCEL_ORDER_RESOURCE = "/api/v1/cancel_order.do"
        params = {
             'api_key':self.api_key,
             'symbol':symbol,
             'order_id':orderId
        }
        params['sign'] = self._build_my_sign(params)
        return self._http_post(CANCEL_ORDER_RESOURCE, params)

    #Spot order information inquiry
    def orderinfo(self, symbol, orderId):
         ORDER_INFO_RESOURCE = "/api/v1/order_info.do"
         params = {
             'api_key':self.api_key,
             'symbol':symbol,
             'order_id':orderId
         }
         params['sign'] = self._build_my_sign(params)
         return self._http_post(ORDER_INFO_RESOURCE, params)

    #Spot bulk order information query
    def ordersinfo(self, symbol, orderId, tradeType):
         ORDERS_INFO_RESOURCE = "/api/v1/orders_info.do"
         params = {
             'api_key':self.api_key,
             'symbol':symbol,
             'order_id':orderId,
             'type':tradeType
         }
         params['sign'] = self._build_my_sign(params)
         return self._http_post(ORDERS_INFO_RESOURCE, params)

    #Spot to get historical order information
    def orderHistory(self, symbol, status, currentPage, pageLength):
           ORDER_HISTORY_RESOURCE = "/api/v1/order_history.do"
           params = {
              'api_key':self.api_key,
              'symbol':symbol,
              'status':status,
              'current_page':currentPage,
              'page_length':pageLength
           }
           params['sign'] = self._build_my_sign(params)
           return self._http_post(ORDER_HISTORY_RESOURCE, params)

    def _build_my_sign(self, params):
        sign = ''
        for key in sorted(params.keys()):
            sign += key + '=' + str(params[key]) + '&'
        data = sign + 'secret_key=' + self.secret_key
        return hashlib.md5(data.encode("utf8")).hexdigest().upper()

    def _http_get(self, resource, params=''):
        conn = http.client.HTTPSConnection(self.api_server, timeout=self.timeout)
        conn.request("GET", resource + '?' + params)
        response = conn.getresponse()
        data = response.read().decode('utf-8')
        return json.loads(data)

    def _http_post(self, resource, params):
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
        }
        conn = http.client.HTTPSConnection(self.api_server, timeout=self.timeout)
        temp_params = urllib.parse.urlencode(params)
        conn.request("POST", resource, temp_params, headers)
        response = conn.getresponse()
        data = response.read().decode('utf-8')
        params.clear()
        conn.close()
        return data
