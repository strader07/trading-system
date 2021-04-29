import asyncio
import datetime
from paf.tardis_client.tardis_feed import TardisFeed
from paf.tardis_client.book import Book
from paf.util.time import datetime_to_str


async def booksbuilder(markets, dates, spot_exchanges):
    orderbooks = {}
    for market in markets:
        for date in dates:
            start = date[0]
            end = date[1]
            if isinstance(start, datetime.datetime) and isinstance(
                end, datetime.datetime
            ):
                start = datetime_to_str(start)
                end = datetime_to_str(end)

            feed = TardisFeed(market.exchange, market, start, end, True, True, spot_exchanges)
            await feed.replay()

            orderbooks[market.market] = Book(
                market.exchange, market.market, start, end, feed.messages
            )
    return orderbooks


async def tradesbuilder(markets, dates):
    orderbooks = {}
    for market in markets:
        for date in dates:
            start = date[0]
            end = date[1]
            if isinstance(start, datetime.datetime) and isinstance(
                end, datetime.datetime
            ):
                start = datetime_to_str(start)
                end = datetime_to_str(end)
            feed = TardisFeed(market.exchange, market, start, end, True, True)
            await feed.replay()
            orderbooks[market.market] = Book(
                market.exchange, market.market, start, end, feed.messages
            )
    return orderbooks
