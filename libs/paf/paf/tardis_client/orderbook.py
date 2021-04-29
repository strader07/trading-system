from collections import deque
from sortedcontainers import SortedDict
from paf.events.enums import Side


class Trade:
    def __init__(self, timestamp, symbol, size, price):
        self.timestamp = float(timestamp)
        self.symbol = symbol
        self.size = float(size)
        self.price = price


class OrderBook(object):
    def __init__(self):
        self.trades = deque()
        self.bids = SortedDict()
        self.asks = SortedDict()

    def update_level(self, side, size, price):
        if side == Side.BID:
            target = self.bids
        if side == Side.ASK:
            target = self.asks

        if float(size) == 0:
            if price in list(target.keys()):
                del target[price]
        else:
            target[price] = size

    def clear_level(self):
        self.bids = SortedDict()
        self.asks = SortedDict()

    def add_trade(self, timestamp, symbol, size, price):
        trade = Trade(timestamp, symbol, size, price)
        self.trades.appendleft(trade)

        return trade
