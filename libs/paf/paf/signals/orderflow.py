import math
from paf.util.time import daterange


class SigOrderFlow:
    def __init__(self, book, max_len=10):
        self.book = book
        self.trades = []
        self.all_trades = []
        self.orderflow = 0
        self.max_len = max_len

        self.order_flows = []

        self.matching_flow_trade = []
        self.unmatching_flow_trade = []
        self.neutral_flow = []

    def trade_at(self, idx):
        return self.all_trades[idx]

    def positive_flow(self):
        return (o[1] for o in self.order_flows if o[1] > 0)

    def negative_flow(self):
        return (abs(o[1]) for o in self.order_flows if o[1] < 0)

    def iterate_by_time(self, unit, start_date, end_date):
        idx = 0
        for date in daterange(unit, start_date, end_date):
            for i in range(idx, len(self.all_trades)):
                if self.all_trades[i].date <= date:
                    idx += 1
            yield date, min(idx, len(self.all_trades) - 1)

    def orderflow_slice(self, idx, window, now):
        start = max(idx - window, 0)
        space = self.all_trades[start:idx]

        flow = 0
        for t in space:
            seconds = (now - t.date).seconds
            side_factor = 1 if t.side == "buy" else -1
            orderflow = t.price * t.size * side_factor * math.exp(-seconds / 60)
            flow += orderflow
        return flow

    def on_trade(self, book, trade):
        self.all_trades.append(trade)
        self.trades.append(trade)
        if len(self.trades) > self.max_len:
            self.trades.pop(0)

        now = trade.date
        flow = 0
        for t in self.trades:
            seconds = (now - t.date).seconds
            side_factor = 1 if t.side == "buy" else -1
            orderflow = t.price * t.size * side_factor * math.exp(-seconds / 60)
            flow += orderflow

        mid = book.top_bid_price + (book.top_ask_price - book.top_bid_price) / 2
        self.order_flows.append((now, flow, mid))

    def on_trade_flow_match(self, book, trade):
        self.on_trade(book, trade)

        if len(self.order_flows) < 2:
            return

        # did this trade match last orderflow direction?
        last_orderflow = self.order_flows[-2]
        flow = last_orderflow[1]

        flow_side = "neutral"
        if flow > 0:
            flow_side = "buy"
        elif flow < 0:
            flow_side = "sell"

        if flow_side == "neutral":
            self.neutral_flow.append(flow)

        elif flow_side == trade.side:
            self.matching_flow_trade.append((flow, trade.price * trade.size))

        elif flow_side != trade.side:
            self.unmatching_flow_trade.append((flow, trade.price * trade.size))
