import asyncio
import os
from paf.tardis_client import booksbuilder, tradesbuilder
from paf.util import setup_uvloop
from process_orderflow import process_orderflow


books = ["BTC-PERP"]
dates = [("2020-02-11T00:00:00", "2020-02-11T02:00:00")]
windows = [2]

# builders need to be updated to take in Market objects


async def lob():
    orderbooks = await booksbuilder(books, dates)
    for sym, book in orderbooks.items():
        book_df, trades_df = book.build_lob()
        if not book_df.empty:
            print(book_df.head())
        if not trades_df.empty:
            print(trades_df.head())


async def trades_lob():
    orderbooks = await tradesbuilder(books, dates)
    for _, book in orderbooks.items():
        trades_df = book.build_trades()
        if not trades_df.empty:
            print(trades_df.head())


async def orderflow():
    orderbooks = await booksbuilder(books, dates)
    for book in orderbooks:
        df, orderflows_by_window = process_orderflow(book, windows)
        print(df)


setup_uvloop()
# asyncio.run(orderflow())
asyncio.run(trades_lob())
asyncio.run(lob())
