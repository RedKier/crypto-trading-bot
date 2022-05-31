import tkinter as tk
import logging
from connectors.binance_futures import BinanceFuturesClient
from interface.root_component import Root

binance_api_key = "yyy"
binance_api_secret = "xxx"

logger = logging.getLogger()

logger.setLevel(logging.INFO)

stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s')
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler('info.log')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

if __name__ == '__main__':
    binance = BinanceFuturesClient(testnet=True, public_key=binance_api_key, secret_key=binance_api_secret)

    root = Root(binance)

    root.mainloop()
