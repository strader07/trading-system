import logging
from datetime import datetime
from paf.events.enums import Side
from hft_orderbook import L2Book, Order


class FastBook:
    def __init__(self, symbol, from_date, to_date, messages):
        self.symbol = symbol
        self.from_date = from_date
        self.to_date = to_date
        self.messages = messages
        self.book = None

        self.snapshot_cb = None
        self.update_cb = None
        self.trade_cb = None

    def register_snapshot(self, cb):
        self.snapshot_cb = cb

    def register_update(self, cb):
        self.update_cb = cb

    def register_trade(self, cb):
        self.trade_cb = cb

    def trades(self):
        # TODO:
        # for trade in self.book.trades:
        #     t = Trade(
        #         self.symbol,
        #         trade.id_num,
        #         float(data["price"]),
        #         trade.qty,
        #         -1,
        #         -1,
        #         trade.timestamp,
        #     )
        #     yield t
        return

    def build(self):
        for message in self.messages:
            self.on_message(message)

    def process_quote(self, quote):
        is_bid = quote.side == Side.BID
        order = Order(is_bid=is_bid, size=quote.size, price=quote.price)
        self.book.process(order)

    def on_message(self, message):
        if message[0] == "S":
            self.book = L2Book()
            # self.process_quote(message[1])
            # TODO: does not work because we do not know when our snapshot has ended.
            # TODO: Change messages to class and group by events by wrapping each data in array.
            # if self.snapshot_cb:
            #     self.snapshot_cb(self.book)

        elif message[0] == "Q":
            self.process_quote(message[1])
            if self.update_cb:
                self.update_cb(self.book)

        elif message[0] == "T":
            trade = message[1]
            self.book.add_trade(trade)
            if self.trade_cb:
                self.trade_cb(self.book, trade)
