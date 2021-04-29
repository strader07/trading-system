import requests
from mwzpyutil.types import Market, MarketType
from ftx_client.api import FTXData


async def ftx_markets(expiry):
    ftx_data = FTXData("", "", [], [])
    markets = await ftx_data.get_markets()
    expired = await ftx_data.get_expired_futures(expiry)
    return markets + expired


def gateio_markets(expiry):
    r = requests.get("https://api.gateio.ws/api/v4/spot/currency_pairs")
    data = r.json()
    markets = []
    for market in data:
        if market["base"] != "JNT" and market["id"] != "BTC_USDT":
            continue

        our_market = Market(
            exchange="gateio",
            market=market["id"],
            instrument=market["id"].replace("_", ""),
            type_=MarketType["spot"],
            enabled=True,
            maker_fee=0,
            taker_fee=0,
            tick_size=0,
            min_size=0,
            price_precision=0,
            size_precision=0,
            mm_size=0,
            expiry=None,
        )

        markets.append(our_market)

    return markets


async def get_markets(exchange, expiry):
    if exchange == "ftx":
        return await ftx_markets(expiry)
    elif exchange == "gateio":
        return gateio_markets(expiry)
    else:
        raise ValueError(
            f"Unable to retrieve instruments. Invalid exchange: {exchange}"
        )
