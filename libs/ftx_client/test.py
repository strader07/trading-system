import asyncio
from ftx_client.api import FTXData


async def on_trade(data, market):
    print(f"Trade: {data}\n")


async def on_raw_trade(data):
    print(f"Raw trade: {data}\n")


async def on_book(data):
    print(f"Book: {data}")


async def main2():
    ftx_data = FTXData(
        "", "", [], [], trades_markets=["BTC-PERP"], book_markets=["BTC-PERP"]
    )
    ftx_data.set_historical_mode("2020-02-10", "2020-02-10T02:00:00")
    ftx_data.register_on_book(on_book)
    ftx_data.register_on_raw_trade(on_raw_trade)
    await ftx_data.subscribe_book()


async def main():
    ftx_data = FTXData(
        "", "", [], [], trades_markets=["BTC-PERP"], book_markets=["BTC-PERP"]
    )
    ftx_data.set_historical_mode("2020-02-10", "2020-02-10T02:00:00")
    # ftx_data.register_on_trade(on_trade)
    ftx_data.register_on_raw_trade(on_raw_trade)
    # ftx_data.register_on_book(on_book)
    await ftx_data.subscribe_book()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    #  loop.run_until_complete(main())
    loop.run_until_complete(main2())
