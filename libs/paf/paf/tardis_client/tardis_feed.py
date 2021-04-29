import os
import json
import aiohttp
import logging
from urllib.parse import quote_plus

from paf.tardis_client.instruments import get_markets
from paf.events import Trade, Quote, Side

import pendulum


class TardisFeed:
    def __init__(
        self, exchange, market, from_date, to_date, orderbook=False, trades=False, spot_exchanges=[]
    ):
        self.got_snapshot = False
        self.trades_markets = [market.market] if trades else []
        self.book_markets = [market.market] if orderbook else []

        dataTypes = ["trade", "book_change"]
        if exchange not in spot_exchanges:
            dataTypes += ["liquidation"]

        if exchange == "gateio":
            exchange = "gate-io"

        self.exchange = exchange
        self.symbol = market.market
        self.from_date = from_date
        self.to_date = to_date
        self.raw_messages = []
        self.liquidations = []

        # Google auth
        self.baseurl = f"https://muz-tardis:1juBfOmEjzgTABUxAJUqr8TQ@tardis.muwazana.com"

        # url = (
        #     "tardis-machine.development.svc.cluster.local"
        #     if os.environ.get("KUBERNETES_SERVICE_HOST")
        #     else "localhost"
        # )
        # self.baseurl = f"http://{url}:8000"

        self._http_replay_options = {
            "exchange": self.exchange,
            "from": self.from_date,
            "to": self.to_date,
            "symbols": [self.symbol],
            "withDisconnectMessages": True,
            "dataTypes": dataTypes,
        }

    @property
    def messages(self):
        return self.raw_messages

    @staticmethod
    async def get_markets(exchange, expiry):
        return await get_markets(exchange, expiry)

    @staticmethod
    def normalize_price(price):
        return "{:.8f}".format(price)

    def process_snapshot(self, data):
        bids = []
        asks = []
        if self.exchange != 'gate-io':
            time = data["timestamp"]
        else:
            time = data["localTimestamp"]
        utcdt = pendulum.parse(time)
        timestamp = utcdt.timestamp()
        dt = utcdt.replace(tzinfo=None)

        for bid in data["bids"]:
            price = self.normalize_price(bid["price"])
            bids.append(
                Quote(self.symbol, price, str(bid["amount"]), Side.BID, dt, timestamp)
            )

        for ask in data["asks"]:
            price = self.normalize_price(ask["price"])
            asks.append(
                Quote(self.symbol, price, str(ask["amount"]), Side.ASK, dt, timestamp)
            )

        self.raw_messages.append(("S", (bids, asks)))

    def process_quote(self, data):
        bids = []
        asks = []
        if self.exchange != 'gate-io':
            time = data["timestamp"]
        else:
            time = data["localTimestamp"]
        utcdt = pendulum.parse(time)
        timestamp = utcdt.timestamp()
        dt = utcdt.replace(tzinfo=None)

        for bid in data["bids"]:
            price = self.normalize_price(bid["price"])
            bids.append(
                Quote(self.symbol, price, str(bid["amount"]), Side.BID, dt, timestamp)
            )

        for ask in data["asks"]:
            price = self.normalize_price(ask["price"])
            asks.append(
                Quote(self.symbol, price, str(ask["amount"]), Side.ASK, dt, timestamp)
            )

        self.raw_messages.append(("Q", (bids, asks)))

    def process_trade(self, data):
        time = data["timestamp"]
        utcdt = pendulum.parse(time)
        timestamp = utcdt.timestamp()
        dt = utcdt.replace(tzinfo=None)

        price = self.normalize_price(data["price"])

        trade = Trade(
            self.symbol,
            data["id"],
            price,
            str(data["amount"]),
            Side.from_string(data["side"]),
            False,
            dt,
            timestamp,
        )
        self.raw_messages.append(("T", trade))

    def on_message(self, message):
        _type = message["type"]

        if _type == "book_change":
            snapshot = message["isSnapshot"]
            if snapshot:
                self.process_snapshot(message)
            else:
                self.process_quote(message)

        elif _type == "book_snapshot":
            name = message["name"]
            if name == "quote":
                self.process_quote(message)
            else:
                self.process_snapshot(message)

        elif _type == "trade":
            self.process_trade(message)

        elif _type == "liquidation":
            self.liquidations.append(message["id"])

    async def replay_normalized_via_tardis_machine(self, replay_options):
        timeout = aiohttp.ClientTimeout(total=0)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            encoded_options = quote_plus(json.dumps(replay_options))
            url = f"{self.baseurl}/replay-normalized?options={encoded_options}"

            async with session.get(url) as response:
                response.content._high_water = 100_000_000

                async for line in response.content:
                    yield line

    async def replay(self):
        replay_options = self._http_replay_options
        lines = self.replay_normalized_via_tardis_machine(replay_options)

        async for line in lines:
            data = json.loads(line)
            if isinstance(data, str):
                err = f"Error: {data}"
                logging.error(err)
                raise RuntimeError(err)

            self.on_message(data)

        self.raw_messages.append(("L", self.liquidations))
