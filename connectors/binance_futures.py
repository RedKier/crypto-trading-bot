import logging
import requests
import time
import typing

from urllib.parse import urlencode

import hmac
import hashlib

import websocket
import json

import threading

from models import *
from strategies import BreakoutStrategy, TechnicalStrategy

logger = logging.getLogger()

socket_url = "wss://fstream.binance.com"


class BinanceFuturesClient:
    def __init__(self, public_key: str, secret_key: str, testnet: bool):
        if testnet:
            self._base_url = "https://testnet.binancefuture.com"
            self._wss_url = "wss://stream.binancefuture.com/ws"
        else:
            self._base_url = "https://fapi.binance.com"
            self._wss_url = "wss://fstream.binance.com/ws"

        self._ws_id = 1
        self.ws: websocket.WebSocketApp
        self.reconnect = True
        self._public_key = public_key
        self._secret_key = secret_key
        self.prices = dict()
        self._headers = {'X-MBX-APIKEY': self._public_key}
        self.contracts = self.get_contracts()
        self.balances = self.get_balances()

        self.logs = []
        self.strategies: typing.Dict[int, typing.Union[TechnicalStrategy, BreakoutStrategy]] = dict()

        t = threading.Thread(target=self._start_ws)
        t.start()

        logger.info('Binance Futures Client successfully initialized')

    def _add_log(self, msg: str):
        logger.info("%s", msg)
        self.logs.append({"log": msg, "displayed": False})

    def _generate_signature(self, data: typing.Dict) -> str:
        return hmac.new(self._secret_key.encode(), urlencode(data).encode(), hashlib.sha256).hexdigest()

    def _make_request(self, method: str, endpoint: str, data):
        if method == "GET":
            try:
                response = requests.get(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None
        elif method == "POST":
            try:
                response = requests.post(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None
        elif method == "DELETE":
            try:
                response = requests.delete(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None
        else:
            raise ValueError()

        if response.status_code == 200:
            return response.json()
        else:
            logger.error("Error while making %s request to %s: %s (error code %s)",
                         method, endpoint, response.json(), response.status_code)

    def get_contracts(self) -> typing.Dict[str, Contract]:
        exchange_info = self._make_request("GET", "/fapi/v1/exchangeInfo", dict())

        if exchange_info is not None:
            contracts = dict()
            for contract_data in exchange_info["symbols"]:
                contracts[contract_data['symbol']] = Contract(contract_data, 'binance')

            return contracts

    def get_historical_candles(self, contract: Contract, interval: str) -> typing.List[Candle]:
        data = dict()
        data['symbol'] = contract.symbol
        data['interval'] = interval
        data['limit'] = 1000

        raw_candles = self._make_request("GET", "/fapi/v1/klines", data)

        candles = []

        if raw_candles is not None:
            for candle_data in raw_candles:
                candles.append(Candle(candle_data, interval, 'binance'))

        return candles

    def get_bid_ask(self, contract: Contract) -> typing.Dict[str, float]:
        data = dict()
        data["symbol"] = contract.symbol
        ob_data = self._make_request("GET", "/fapi/v1/ticker/bookTicker", data)

        if ob_data is not None:
            if contract.symbol not in self.prices:
                self.prices[contract.symbol] = {"bid": float(ob_data["bidPrice"]), "ask": float(ob_data["askPrice"])}
            else:
                self.prices[contract.symbol]['bid'] = float(ob_data["bidPrice"])
                self.prices[contract.symbol]['ask'] = float(ob_data["askPrice"])

            return self.prices[contract.symbol]

    def get_balances(self) -> typing.Dict[str, Balance]:
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        balances = dict()

        account_data = self._make_request("GET", "/fapi/v1/account", data)

        if account_data is not None:
            for assets_data in account_data['assets']:
                balances[assets_data['asset']] = Balance(assets_data)

        return balances

    def place_order(self, contract: Contract, order_type: str, quantity: float,
                    side: str, price=None, tif=None) -> OrderStatus:

        data = dict()
        data['symbol'] = contract.symbol
        data['side'] = side.upper()
        data['quantity'] = quantity
        data['type'] = order_type
        data['timestamp'] = int(time.time() * 1000)

        if price is not None:
            data['price'] = price

        if tif is not None:
            data['timeInForce'] = tif

        data['signature'] = self._generate_signature(data)

        order_status = self._make_request("POST", "/fapi/v1/order", data)

        if order_status is not None:
            order_status = OrderStatus(order_status)

        return order_status

    def cancel_order(self, contract: Contract, order_id: int) -> OrderStatus:
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['symbol'] = contract.symbol
        data['orderId'] = order_id
        data['signature'] = self._generate_signature(data)

        order_status = self._make_request("DELETE", "/fapi/v1/order", data)

        if order_status is not None:
            order_status = OrderStatus(order_status)

        return order_status

    def get_order_status(self, contract: Contract, order_id: int) -> OrderStatus:
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['symbol'] = contract.symbol
        data['orderId'] = order_id
        data['signature'] = self._generate_signature(data)

        order_status = self._make_request("GET", "/fapi/v1/order", data)

        if order_status is not None:
            order_status = OrderStatus(order_status)

        return order_status

    def _start_ws(self):
        self.ws = websocket.WebSocketApp(self._wss_url, on_open=self._on_open, on_close=self._on_close,
                                         on_error=self._on_error,
                                         on_message=self._on_message)

        while True:
            try:
                if self.reconnect:
                    self.ws.run_forever()
                else:
                    break
            except Exception as e:
                logger.error("Websocket error in run_forever() method: %s", e)
            time.sleep(2)

    def _on_open(self, ws):
        logger.info("Binance websocket connection established.")
        self.subscribe_channel(list(self.contracts.values()), "bookTicker")

    def _on_close(self, ws, close_status_code, close_msg):
        logger.warning("Binance websocket connection closed.")
        self.ws_connected = False

    def _on_error(self, ws, msg: str):
        logger.error("Binance websocket error: %s", msg)

    def _on_message(self, ws, msg: str):
        data = json.loads(msg)

        if "e" in data:
            if data['e'] == "bookTicker":
                symbol = data['s']

                if symbol not in self.prices:
                    self.prices[symbol] = {"bid": float(data["b"]), "ask": float(data["a"])}
                else:
                    self.prices[symbol]['bid'] = float(data["b"])
                    self.prices[symbol]['ask'] = float(data["a"])
                try:
                    for b_index, strat in self.strategies.items():
                        if strat.contract.symbol == symbol:
                            for trade in strat.trades:
                                if trade.status == "open" and trade.entry_prize is not None:
                                    if trade.side == 'long':
                                        trade.pnl = (self.prices[symbol]['bid'] - trade.entry_prize) * trade.quantity
                                    elif trade.side == 'short':
                                        trade.pnl = (trade.entry_prize - self.prices[symbol]['bid']) * trade.quantity
                except RuntimeError as e:
                    logger.error(f"Error while looping through the Binance Strategies: {e}")

            elif data['e'] == "aggTrade":

                symbol = data['s']

                for key, strat in self.strategies.items():
                    if strat.contract.symbol == symbol:
                        res = strat.parse_trades(float(data['p']), float(data['q']), data['T'])
                        strat.check_trade(res)

    def subscribe_channel(self, contracts: typing.List[Contract], channel: str):
        data = dict()
        data['method'] = "SUBSCRIBE"
        data['params'] = []

        for contract in contracts:
            data['params'].append(contract.symbol.lower() + "@" + channel)
        data['id'] = self._ws_id
        try:
            self.ws.send(json.dumps(data))
        except Exception as e:
            logger.error("Websocket error while subscribing to %s %s updates: %s", len(contracts), channel, e)
            return None

        self._ws_id += 1

    def get_trade_size(self, contract: Contract, price: float, balance_pct: float):
        balance = self.get_balances()

        if balance is not None:
            if 'USDT' in balance:
                balance = balance['USDT'].wallet_balance
            else:
                return None
        else:
            return None

        trade_size = (balance * balance_pct / 100) / price

        trade_size = round(round(trade_size / contract.lot_size) * contract.lot_size, 8)

        logger.info("Binance Futures current USDT balance = %s, trade size = %s", balance, trade_size)

        return trade_size
