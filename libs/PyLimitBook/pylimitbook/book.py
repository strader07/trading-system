#!/usr/bin/python

from collections import deque

from pylimitbook.tick import Bid, Ask, Trade
from pylimitbook.tree import Tree
from builtins import input
from six.moves import cStringIO as StringIO
from sortedcontainers import SortedDict


def parse_csv(columns, line):
    """
    Parse a CSV line that has ',' as a separator.
    Columns is a list of the column names, must match the number of
    comma-separated values in the input line.
    """
    data = {}
    split = line.split(",")
    for idx, name in enumerate(columns):
        data[name] = split[idx]
    return data


class Book(object):
    def __init__(self):
        self.trades = deque(maxlen=100)  # Index [0] is most recent trade
        self.bids = Tree()
        self.asks = Tree()
        self.last_tick = None
        self.last_timestamp = 0
        self.save_tseries = False
        self.time_series = SortedDict()

    def process_bid_ask(self, tick):
        """
        Generic method to process bid or ask.
        """
        tree = self.bids if tick.is_bid else self.asks

        if tick.qty == 0:
            # Quantity is zero -> remove the entry
            tree.remove_order_by_id(tick.id_num)
        else:
            if tree.order_exists(tick.id_num):
                tree.update_order(tick)
            else:
                # New order
                tree.insert_tick(tick)

        if self.save_tseries:
            tick_type = "B" if tick.is_bid else "A"
            self.time_series[tick.timestamp] = (tick_type, tick)

    def process_l2_bid_ask(self, tick):
        """
        Generic method to process level 2 bid or ask.
        """
        tree = self.bids if tick.is_bid else self.asks

        if tick.qty == 0:
            # Quantity is zero -> remove the entry
            tree.remove_price(tick.price)
        else:
            if tree.price_exists(tick.price):
                tree.update_price_level(tick)
            else:
                # New order
                tree.insert_tick(tick)

    def bid(self, csv):
        columns = ["event", "symbol", "exchange", "id_num", "qty", "price", "timestamp"]
        data = parse_csv(columns, csv)
        bid = Bid(data)
        if bid.timestamp > self.last_timestamp:
            self.last_timestamp = bid.timestamp
        self.last_tick = bid
        self.process_bid_ask(bid)
        return bid

    def bid_split(self, symbol, id_num, qty, price, timestamp):
        data = {"timestamp": timestamp, "qty": qty, "price": price, "id_num": id_num}
        bid = Bid(data)
        if bid.timestamp > self.last_timestamp:
            self.last_timestamp = bid.timestamp
        self.last_tick = bid
        self.process_bid_ask(bid)
        return bid

    def bid_level(self, symbol, id_num, qty, price, timestamp):
        data = {"timestamp": timestamp, "qty": qty, "price": price, "id_num": id_num}
        bid = Bid(data)
        if bid.timestamp > self.last_timestamp:
            self.last_timestamp = bid.timestamp
        self.last_tick = bid
        self.process_l2_bid_ask(bid)
        return bid

    def ask(self, csv):
        columns = ["event", "symbol", "exchange", "id_num", "qty", "price", "timestamp"]
        data = parse_csv(columns, csv)
        ask = Ask(data)
        if ask.timestamp > self.last_timestamp:
            self.last_timestamp = ask.timestamp
        self.last_tick = ask
        self.process_bid_ask(ask)
        return ask

    def ask_split(self, symbol, id_num, qty, price, timestamp):
        data = {"timestamp": timestamp, "qty": qty, "price": price, "id_num": id_num}
        ask = Ask(data)
        if ask.timestamp > self.last_timestamp:
            self.last_timestamp = ask.timestamp
        self.last_tick = ask
        self.process_bid_ask(ask)
        return ask

    def ask_level(self, symbol, id_num, qty, price, timestamp):
        data = {"timestamp": timestamp, "qty": qty, "price": price, "id_num": id_num}
        ask = Ask(data)
        if ask.timestamp > self.last_timestamp:
            self.last_timestamp = ask.timestamp
        self.last_tick = ask
        self.process_l2_bid_ask(ask)
        return ask

    def trade(self, csv):
        columns = ["event", "symbol", "exchange", "id_num", "qty", "price", "timestamp"]
        data = parse_csv(columns, csv)
        data["id_num"] = 0
        trade = Trade(data)
        if trade.timestamp > self.last_timestamp:
            self.last_timestamp = trade.timestamp
        self.last_tick = trade
        self.trades.appendleft(trade)
        if self.save_tseries:
            self.time_series[trade.timestamp] = ("T", trade)
        return trade

    def trade_split(self, symbol, qty, price, timestamp):
        data = {"timestamp": timestamp, "qty": qty, "price": price, "id_num": 0}
        trade = Trade(data)
        if trade.timestamp > self.last_timestamp:
            self.last_timestamp = trade.timestamp
        self.last_tick = trade
        self.trades.appendleft(trade)
        if self.save_tseries:
            self.time_series[trade.timestamp] = ("T", trade)
        return trade

    def str_levels(self, levels):
        # Efficient string concat
        file_str = StringIO()
        file_str.write("\n------ Asks -------\n")
        if self.asks != None and len(self.asks) > 0:
            for k, v in reversed(self.asks.price_tree.items()[:levels]):
                file_str.write("%s" % v)
        file_str.write("------ Bids -------\n")
        if self.bids != None and len(self.bids) > 0:
            for k, v in reversed(self.bids.price_tree.items()[:levels]):
                file_str.write("%s" % v)
        file_str.write("\n------ Trades ------\n")
        if self.trades != None and len(self.trades) > 0:
            num = 0
            for entry in self.trades:
                if num < 5:
                    file_str.write(
                        str(entry.qty)
                        + " @ "
                        + str(entry.price / 100000000)
                        + " ("
                        + str(entry.timestamp)
                        + ")\n"
                    )
                    num += 1
                else:
                    break
        file_str.write("\n")
        return file_str.getvalue()

    def __str__(self):
        # Efficient string concat
        file_str = StringIO()
        file_str.write("\n------ Asks -------\n")
        if self.asks != None and len(self.asks) > 0:
            for k, v in reversed(self.asks.price_tree.items()):
                file_str.write("%s" % v)
        file_str.write("------ Bids -------\n")
        if self.bids != None and len(self.bids) > 0:
            for k, v in reversed(self.bids.price_tree.items()):
                file_str.write("%s" % v)
        file_str.write("\n------ Trades ------\n")
        if self.trades != None and len(self.trades) > 0:
            num = 0
            for entry in self.trades:
                if num < 5:
                    file_str.write(
                        str(entry.qty)
                        + " @ "
                        + str(entry.price / 100000000)
                        + " ("
                        + str(entry.timestamp)
                        + ")\n"
                    )
                    num += 1
                else:
                    break
        file_str.write("\n")
        return file_str.getvalue()
