class Balance:
    def __init__(self, info):
        self.initial_margin = float(info['initialMargin'])
        self.maintenance_margin = float(info['maintMargin'])
        self.margin_balance = float(info['marginBalance'])
        self.wallet_balance = float(info['walletBalance'])
        self.unrealized_pln = float(info['unrealizedProfit'])


class Candle:
    def __init__(self, candle_info, timeframe, exchange):
        if exchange == 'binance':
            self.timestamp = candle_info[0]
            self.open = float(candle_info[1])
            self.high = float(candle_info[2])
            self.low = float(candle_info[3])
            self.close = float(candle_info[4])
            self.volume = float(candle_info[5])

        elif exchange == 'parse_trade':
            self.timestamp = candle_info["ts"]
            self.open = float(candle_info["open"])
            self.high = float(candle_info["high"])
            self.low = float(candle_info["low"])
            self.close = float(candle_info["close"])
            self.volume = float(candle_info["volume"])


class Contract:
    def __init__(self, contract_info, exchange):
        self.symbol = contract_info['symbol']
        self.base_asset = contract_info['baseAsset']
        self.quote_asset = contract_info['quoteAsset']
        self.price_decimals = contract_info['pricePrecision']
        self.quantity_decimals = contract_info['quantityPrecision']
        self.tick_size = 1 / pow(10, contract_info['pricePrecision'])
        self.lot_size = 1 / pow(10, contract_info['quantityPrecision'])
        self.exchange = exchange


class OrderStatus:
    def __init__(self, order_info):
        self.order_id = order_info['orderId']
        self.status = order_info['status'].lower()
        self.avg_price = float(order_info['avgPrice'])


class Trade:
    def __init__(self, trade_info):
        self.time: int = trade_info['time']
        self.contract: Contract = trade_info['contract']
        self.strategy: str = trade_info['strategy']
        self.side: str = trade_info['side']
        self.entry_prize: float = trade_info['entry_prize']
        self.status: str = trade_info['status']
        self.pnl: float = trade_info['pnl']
        self.quantity = trade_info['quantity']
        self.entry_id: float = trade_info['entry_id']


