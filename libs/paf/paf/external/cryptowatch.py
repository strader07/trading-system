from cryptowatch_client import Client
from paf.events import MarketSummary
from datetime import datetime
import pandas as pd


class CryptoWatch:
    def __init__(self):
        self.market_summary = MarketSummary(0, 0, 0, 0, 0)
        self.client = Client(timeout=30)

    def get_markets_summary(self, exchange, pair):

        summary = self.client.get_markets_summary(exchange=exchange, pair=pair).json()[
            "result"
        ]

        price = summary["price"]
        self.market_summary.last_price = price["last"]
        self.market_summary.high_price = price["high"]
        self.market_summary.low_price = price["low"]

        change = price["change"]
        self.market_summary.pct_change = change["percentage"]
        self.market_summary.abs_change = change["absolute"]

    def get_markets_ohlc(self, exchange, pair, before, after, period):
        before = datetime.strptime(before, "%Y-%m-%d %H:%M:%S")
        before = int(datetime.timestamp(before))

        after = datetime.strptime(after, "%Y-%m-%d %H:%M:%S")
        after = int(datetime.timestamp(after))
        string_period = ",".join(map(str, period))

        ohlc = self.client.get_markets_ohlc(
            exchange=exchange,
            pair=pair,
            before=before,
            after=after,
            periods=string_period,
        )

        data = ohlc.json()["result"]
        # create dict
        dictionary = {}

        list_period = period

        for entry in list_period:
            out = data[str(entry)]
            df = pd.DataFrame(
                out,
                columns=[
                    "close_time",
                    "open_price",
                    "high_price",
                    "low_price",
                    "close_price",
                    "volume",
                    "volume_quote",
                ],
            )
            df["close_time"] = pd.to_datetime(df["close_time"], unit="s")
            dictionary.update({str(entry): df})
        return dictionary
