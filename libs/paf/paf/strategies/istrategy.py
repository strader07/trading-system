from abc import ABC
from typing import Type

from pylimitbook.researchBook import ResearchBook

from paf.events import MarketSnapshot, MarketRefresh, MDEntryType
from paf.util import WindowManager, date_str_to_timestamp


class IStrategy(ABC):
    def __init__(self, period=0):
        self.book = ResearchBook()
        self.event_id = 0
        self.window_manager = WindowManager(period)

    def process_book(self, mkt_data):
        for entry in mkt_data.MDEntries:
            timestamp = date_str_to_timestamp(entry.MDEntryDate)
            # timestamp = datetime.datetime.strptime(
            #     entry.MDEntryDate, "%Y%m%d-%H:%M:%S.%f"
            # ).timestamp()

            if entry.MDEntryType == MDEntryType.BID:
                self.book.bid_level(
                    mkt_data.Symbol,
                    self.event_id,
                    entry.MDEntrySize,
                    str(entry.MDEntryPx),
                    timestamp,
                )
            elif entry.MDEntryType == MDEntryType.OFFER:
                self.book.ask_level(
                    mkt_data.Symbol,
                    self.event_id,
                    entry.MDEntrySize,
                    str(entry.MDEntryPx),
                    timestamp,
                )
            elif entry.MDEntryType == MDEntryType.TRADE:
                self.book.trade_split(
                    mkt_data.Symbol, entry.MDEntrySize, str(entry.MDEntryPx), timestamp
                )

        self.event_id += 1

    def on_market_snapshot(self, snapshot: Type[MarketSnapshot]):
        self.process_book(snapshot)
        self.on_book_snapshot()

        if self.window_manager.period > 0:
            self.window_manager.subscribe_rollover(self.on_rollover)

    def on_market_refresh(self, refresh: Type[MarketRefresh]):
        old_best_bid = (self.book.top_bid_price, self.book.top_bid_volume)
        old_best_ask = (self.book.top_ask_price, self.book.top_ask_volume)
        last_spread = self.book.spread

        self.process_book(refresh)

        new_best_bid = (self.book.top_bid_price, self.book.top_bid_volume)
        new_best_ask = (self.book.top_ask_price, self.book.top_ask_volume)

        matches = [
            entry
            for entry in refresh.MDEntries
            if entry.MDEntryType == MDEntryType.TRADE
        ]
        if matches:
            if self.window_manager.period > 0:
                for entry in matches:
                    self.window_manager.handle_match(entry)
            self.on_match(refresh.Symbol, matches)

        if last_spread != self.book.spread:
            self.on_spread_update()
        elif old_best_bid != new_best_bid or old_best_ask != new_best_ask:
            self.on_bbo_update()

        self.on_lv2_update()

        if not matches and self.window_manager.period > 0:
            self.window_manager.roll_windows(refresh)

    #
    # Event callbacks
    #

    def on_book_snapshot(self):
        pass

    def on_lv2_update(self):
        pass

    def on_bbo_update(self):
        pass

    def on_spread_update(self):
        pass

    def on_match(self, symbol, matches):
        pass

    def on_rollover(self, window):
        pass
