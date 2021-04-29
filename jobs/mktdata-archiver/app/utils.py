from enum import Enum
import csv
from dataclasses import dataclass
from datetime import date

from mwzpyutil.types import Market, MarketType
from paf.tardis_client.tardis_feed import TardisFeed

import pendulum


def get_markets_file(file, exchange):
    markets = []
    with open(file) as markets_file:
        reader = csv.reader(markets_file, delimiter=",")
        next(reader)
        for row in reader:
            markets.append(
                Market(
                    exchange,
                    row[0],
                    row[1],
                    MarketType[row[2].split(".")[1]],
                    row[3],
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    pendulum.parse(row[4]) if row[4] else None,
                )
            )
    return markets


async def get_markets(config, expiry=None):

    file = config.markets_csv
    if file:
        return get_markets_file(config.exchanges[0], file)

    all_markets = []

    for exchange in config.exchanges:
        markets = await TardisFeed.get_markets(exchange, expiry)
        all_markets.extend(markets)

    return all_markets


@dataclass
class RunSettings:
    date: date
    market: Market
    spot_exchanges: []

    def datestr(self):
        return self.date.strftime("%Y-%m-%d")

    def __str__(self):
        return f"{self.market.exchange}:{self.market.instrument}:{self.datestr()}"


class FileType(Enum):
    BOOK = 1
    TRADES = 2
    REFDATA = 3


@dataclass
class RawFile:
    src: str
    file_type: FileType
