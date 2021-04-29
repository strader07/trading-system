import time

from paf.strategies import IStrategy
from paf.signals import RandomSignal


class Strategy(IStrategy):
    def __init__(self):
        period = 10
        super().__init__(period)
        self.signal = RandomSignal()
        self.signal_value = None

    def on_book_snapshot(self):
        print(self.book)
        print("--")
        print(
            "Snapshot BBO: {} {} | {} {}".format(
                self.book.top_bid_volume,
                self.book.top_bid_price,
                self.book.top_ask_price,
                self.book.top_ask_volume,
            )
        )

    # def on_lv2_update(self):
    #     print(
    #         "LV2 Update: {} {} | {} {}".format(
    #             self.book.top_bid_volume,
    #             self.book.top_bid_price,
    #             self.book.top_ask_price,
    #             self.book.top_ask_volume,
    #         )
    #     )

    def on_bbo_update(self):
        signal = self.signal.process(self.book.midpoint_price)
        if signal is not None and signal != self.signal_value:
            self.signal_value = signal
            signal_str = ""
            if signal == 0:
                signal_str = "flat"
            elif signal == 1:
                signal_str = "buy"
            elif signal == -1:
                signal_str = "sell"
            print(f"Signal: {signal_str}")

    def on_rollover(self, window):
        print(f"Rollover: {time.time()}: {window}")

    # TODO: on market close?
