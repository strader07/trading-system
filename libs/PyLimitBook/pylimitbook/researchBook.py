#!/usr/bin/python

from pylimitbook.book import Book


class ResearchBook(Book):
    def __init__(self):
        super().__init__()
        self.open_time = 34200000  # 9:30 am
        self.close_time = 57600000  # 4:00 pm
        self.millis_in_hour = 3600000
        self.millis_in_minute = 60000
        self.millis_in_second = 1000
        self.top_ask_price_cache = None
        self.top_bid_price_cache = None

    def bid(self, bid):
        self.top_bid_price_cache = None
        return super().bid(bid)

    def bid_split(self, symbol, id, qty, price, timestamp):
        self.top_bid_price_cache = None
        return super().bid_split(symbol, id, qty, price, timestamp)

    def bid_level(self, symbol, id_num, qty, price, timestamp):
        self.top_bid_price_cache = None
        return super().bid_level(symbol, id_num, qty, price, timestamp)

    def ask(self, ask):
        self.top_ask_price_cache = None
        return super().ask(ask)

    def ask_split(self, symbol, id, qty, price, timestamp):
        self.top_ask_price_cache = None
        return super().ask_split(symbol, id, qty, price, timestamp)

    def ask_level(self, symbol, id_num, qty, price, timestamp):
        self.top_ask_price_cache = None
        return super().ask_level(symbol, id_num, qty, price, timestamp)

    def trade(self, trade):
        return super().trade(trade)

    def trade_split(self, symbol, qty, price, timestamp):
        return super().trade_split(symbol, qty, price, timestamp)

    def is_market_open(self):
        if (
            self.last_timestamp >= self.open_time
            and self.last_timestamp < self.close_time
        ):
            return True
        else:
            return False

    @property
    def top_bid_price(self):
        if self.top_bid_price_cache != None:
            return self.top_bid_price_cache / float(100000000)
        elif len(self.bids) == 0:
            return 0
        else:
            self.top_bid_price_cache = self.bids.max()
            return (
                self.top_bid_price_cache / float(100000000)
                if self.top_bid_price_cache
                else 0
            )

    @property
    def top_ask_price(self):
        if self.top_ask_price_cache != None:
            return self.top_ask_price_cache / float(100000000)
        elif len(self.asks) == 0:
            return 0
        else:
            self.top_ask_price_cache = self.asks.min()
            return (
                self.top_ask_price_cache / float(100000000)
                if self.top_ask_price_cache
                else 0
            )

    @property
    def top_bid_volume(self):
        return (
            self.bids.price_map[self.top_bid_price_cache].head_order.tick.qty
            if self.top_bid_price_cache
            else 0
        )

    @property
    def top_ask_volume(self):
        return (
            self.asks.price_map[self.top_ask_price_cache].head_order.tick.qty
            if self.top_ask_price_cache
            else 0
        )

    @property
    def bid_volume(self):
        return self.bids.volume

    @property
    def ask_volume(self):
        return self.asks.volume

    @property
    def spread(self):
        spread = self.top_ask_price - self.top_bid_price
        return spread if spread > 0 else 0

    @property
    def midpoint_price(self):
        if self.spread > 0:
            return self.top_bid_price + (self.spread / 2)
        elif self.top_ask_price > 0 and self.top_bid_price > 0:
            return self.top_bid_price
        else:
            return None

    @property
    def bids_order_count(self):
        return len(self.bids.order_map)

    @property
    def asks_order_count(self):
        return len(self.asks.order_map)
