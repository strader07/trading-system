from datetime import datetime
from paf.util.time import date_from_timestamp


class SigSpread:  # rename to avg spread
    def __init__(self):
        self.last_spread_change = None
        self.spread_per_minute = []
        self.curr_spreads = 0
        self.mid_price_after_minute = []

    def on_spread_update(self, book):
        # TODO: use WindowManager

        dt = date_from_timestamp(book.last_timestamp)
        if (
            not (dt and self.last_spread_change)
            or dt.minute <= self.last_spread_change.minute
        ):
            self.curr_spreads += 1
        else:
            if len(self.spread_per_minute) > 0:
                mid_price = (book.top_bid_price + book.top_ask_price) / 2
                self.mid_price_after_minute.append(mid_price)
            self.spread_per_minute.append(self.curr_spreads)
            self.curr_spreads = 0

        self.last_spread_change = dt
