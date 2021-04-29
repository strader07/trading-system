from paf.events import MatchesWindow
from paf.util.time import date_str_to_timestamp

from copy import deepcopy


class WindowManager:
    def __init__(self, period):
        self.pending_window = MatchesWindow(0, 0, 0, 0, 0, 0)
        self.last_window = MatchesWindow(0, 0, 0, 0, 0, 0)
        self.pending_window_start = 0
        self.period = period
        self.callback = None

    def subscribe_rollover(self, callback):
        self.callback = callback

    def handle_match(self, trade):
        self.roll_windows(trade)

        price = trade.MDEntryPx
        volume = trade.MDEntrySize
        timestamp = date_str_to_timestamp(trade.MDEntryDate)

        if self.pending_window.data_points == 0:
            self.pending_window.max_price = price
            self.pending_window.min_price = price
            self.pending_window.open_price = price
            self.pending_window.volume = 0

        self.pending_window.max_price = max(price, self.pending_window.max_price)
        self.pending_window.min_price = min(price, self.pending_window.min_price)
        self.pending_window.close_price = price
        self.pending_window.volume += volume
        self.pending_window.data_points += 1

    def roll_windows(self, event):
        timestamp = date_str_to_timestamp(event.MDEntryDate)

        if self.pending_window.data_points == 0:
            self.pending_window_start = timestamp

        remaining_timestamp = int(timestamp % self.pending_window_start)

        if remaining_timestamp > self.period:
            self.pending_window_start = timestamp
            self.last_window = deepcopy(self.pending_window)
            self.pending_window = MatchesWindow(0, 0, 0, 0, 0, 0)
            self.callback(self.last_window)
