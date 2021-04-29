import asyncio
import csv
from ftx_client.client import FtxClient

KEY = ""
SECRET = ""
SUBACCOUNTS = [""]
# BOOKS = ["USDT-1227"]


async def get_volumes(client):
    books = ["USDT-1227"]


def print_csv(markets):
    with open("markets_volume.csv", mode="w") as f:
        writer = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Book", "Award", "Volume", "Size"])

        for market in markets:
            award = 1000
            size = 4000
            if "BTC" in market["name"]:
                award = 2500
                size = 20000
            elif (
                "ETH" in market["name"]
                or "XRP" in market["name"]
                or "EOS" in market["name"]
            ):
                award = 1500
                size = 7500
            elif "USDT" in market:
                award = 250

            writer.writerow([market["name"], award, market["volume"], size])


def asset_class_filter(market):
    filter_out = ["/USD", "/BTC", "MOVE", "1227"]
    for f in filter_out:
        if f in market["name"]:
            return False
    return True


async def main():
    for subaccount in SUBACCOUNTS:
        client = FtxClient(KEY, SECRET, subaccount)
        markets = await client.get_markets()
        volumes = [
            {"name": market["name"], "volume": market["volumeUsd24h"]}
            for market in markets
            if "volumeUsd24h" in market
        ]

        volumes = sorted(volumes, key=lambda i: i["volume"], reverse=True)
        volumes = filter(asset_class_filter, volumes)

        # attach hedge book here

        print_csv(volumes)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
