import aiohttp
import asyncio
from tabulate import tabulate
from datetime import datetime, timezone
from urllib.parse import urljoin  # , urlparse, urlencode, quote_plus

from mwzpyutil import Config, connect_redis, TelegramConfig, logger

TELEGRAM = TelegramConfig()


async def send_orders_alert(no_orders):
    msg = "ALERT! No orders in the past 40min.\n"

    table = [["Book", "Last Order"]]
    for book, alert in no_orders.items():
        table.append([book, alert["last_order_date"]])

    msg += tabulate(table)
    path = urljoin(TELEGRAM.base, TELEGRAM.path)
    params = TELEGRAM.get_params(msg)

    async with aiohttp.ClientSession() as session:
        async with session.request("get", urljoin(TELEGRAM.base, path), params=params):
            pass


async def send_stats_alert(no_stats):
    msg = "ALERT! No MMstats in the past 1.5hrs.\n"

    table = [["Book", "Last 3 Deep %", "Last 3 BBO %", "Last Stat Update"]]
    for alert in no_stats:
        table.append(
            [
                alert["book"],
                f"{alert['deep_stat_0']}, {alert['deep_stat_1']}, {alert['deep_stat_1']}",
                f"{alert['bbo_stat_0']}, {alert['bbo_stat_1']}, {alert['bbo_stat_1']}",
                alert["last_mm_stat_date"],
            ]
        )

    msg += tabulate(table)
    path = urljoin(TELEGRAM.base, TELEGRAM.path)
    params = TELEGRAM.get_params(msg)

    async with aiohttp.ClientSession() as session:
        async with session.request(
            "get", urljoin(TELEGRAM.base, path), params=params
        ) as resp:
            pass


class State:
    # All durations are in seconds
    def __init__(self, check_rate, mm_stats_check_rate, connection_check_rate):
        self.open_orders_books = []
        self.book_last_close_date = {}
        self.mmstats_book_to_date = {}

        self.last_check = None
        self.last_stat_check = None

        self.check_rate = check_rate
        self.mm_stats_check_rate = mm_stats_check_rate
        self.connection_check_rate = connection_check_rate

        self.config = None
        self.redis = None

        self.markets = self.get_markets()

    async def connect_redis(self):
        self.config = Config(auth_ftx=False)
        self.redis = await connect_redis(self.config.redis, "redis")
        return self.redis

    def get_markets(self):
        self.config = Config(auth_ftx=False)
        return [
            market
            for mlist in self.config.subaccounts_markets.values()
            for market in mlist
        ]

    def add_order(self, market, date, status):
        if market not in self.markets:
            return
        if status in ("new", "open"):
            self.open_orders_books.append(market)
        elif status == "closed":
            if market in self.open_orders_books:
                self.open_orders_books.remove(market)
            self.book_last_close_date[market] = date

    def add_mmstat(self, market, deep_stat, bbo_stat, date):
        if market not in self.markets:
            return

        if market not in self.mmstats_book_to_date:
            self.mmstats_book_to_date[market] = [(deep_stat, bbo_stat, date)]
        else:
            # Only update stats if we have a diff/new update in the stats
            stat = self.mmstats_book_to_date[market]
            last_stat = stat[-1]
            if last_stat[0] == deep_stat and last_stat[1] == bbo_stat:
                return
            self.mmstats_book_to_date[market].append((deep_stat, bbo_stat, date))

            # Keep history of last two stats only
            if len(self.mmstats_book_to_date[market]) > 3:
                self.mmstats_book_to_date[market].pop(0)

    async def schedule_checks(self):
        while True:
            now = datetime.now(timezone.utc)
            if not self.last_check or self.last_check.day != now.day:
                self.open_orders_books.clear()
                self.book_last_close_date.clear()
                logger.info("New day, cleared orders.")

            alert_books = {}
            for book in self.markets:
                alert_books[book] = {
                    "now": now,
                    "last_order_date": "N/A",
                    "seconds_late": "N/A",
                }

            # Insert if last close date is old
            for book, date in self.book_last_close_date.items():
                diff = now - date
                if diff.total_seconds() >= self.check_rate:
                    alert_books[book] = {
                        "now": now,
                        "last_order_date": date,
                        "seconds_late": diff.total_seconds(),
                    }

            # Remove books with open orders
            for book in self.open_orders_books:
                if book in alert_books:
                    del alert_books[book]

            if alert_books:
                await asyncio.ensure_future(send_orders_alert(alert_books))
            self.last_check = now
            await asyncio.sleep(self.check_rate)

    async def schedule_stats_checks(self):
        while True:
            now = datetime.now(timezone.utc)
            if not self.last_stat_check or self.last_stat_check.day != now.day:
                self.mmstats_book_to_date.clear()
                logger.info("New day, cleared MM stats.")

            alert_stats = []
            processed = False

            for book, stats in self.mmstats_book_to_date.items():
                processed = True
                logger.info(f"Checking BBO stats for {book}:")

                if len(stats) < 3:
                    logger.info("Total day stats less than 3, skipping.")
                    return

                deep_stat_0, bbo_stat_0, date_0 = stats[0]
                deep_stat_1, bbo_stat_1, date_1 = stats[1]
                deep_stat_2, bbo_stat_2, date_2 = stats[2]

                missed_deep = deep_stat_0 < deep_stat_1 < deep_stat_2
                missed_bbo = bbo_stat_0 < bbo_stat_1 < bbo_stat_2

                logger.info(
                    f"Last 3: {stats[0]}, {stats[1]}, {stats[2]}. Missed deep|bbo: {missed_deep}|{missed_bbo}"
                )

                if missed_deep and missed_bbo:
                    alert_stats.append(
                        {
                            "book": book,
                            "now": now,
                            "last_mm_stat_date": date_2,
                            "deep_stat_0": deep_stat_0,
                            "deep_stat_1": deep_stat_1,
                            "deep_stat_2": deep_stat_2,
                            "bbo_stat_0": bbo_stat_0,
                            "bbo_stat_1": bbo_stat_1,
                            "bbo_stat_2": bbo_stat_2,
                        }
                    )

            if alert_stats:
                await asyncio.ensure_future(send_stats_alert(alert_stats))
            self.last_stat_check = now
            if processed:
                logger.info("============")
            await asyncio.sleep(self.mm_stats_check_rate)

    async def connection_check(self):
        while True:
            try:
                # check connection
                res = await self.redis.ping()
                if res != b"PONG":
                    logger.warning("Connection lost. Reconnecting...")
                    await send_to_telegram("WARNING! Connection lost. Reconnecting...")
                    self.redis = await connect_redis(self.config.redis, "redis")

                # check subscriptions
                subs = await self.redis.pubsub_numsub(
                    "stream:ftx:orders", "public:ftx:mmstats"
                )
                if subs[b"stream:ftx:orders"] == 0:
                    logger.warning(
                        "Subscription to stream:ftx:orders lost. Resubscribing..."
                    )
                    await send_to_telegram(
                        "WARNING! Subscription to stream:ftx:orders lost. Resubscribing..."
                    )
                    self.open_orders_books.clear()
                    self.book_last_close_date.clear()
                    asyncio.ensure_future(self.consume_orders())
                if subs[b"public:ftx:mmstats"] == 0:
                    logger.warning(
                        "Subscription to public:ftx:mmstats lost. Resubscribing..."
                    )
                    await send_to_telegram(
                        "WARNING! Subscription to public:ftx:mmstats lost. Resubscribing..."
                    )
                    self.mmstats_book_to_date.clear()
                    asyncio.ensure_future(self.consume_mmstats())
            except:
                if not self.redis or self.redis.closed:
                    logger.warning("Connection lost. Reconnecting...")
                    await send_to_telegram("WARNING! Connection lost. Reconnecting...")
                    self.redis = await connect_redis(self.config.redis, "redis")

            await asyncio.sleep(self.connection_check_rate)

    async def consume_orders(self):
        channels = await self.redis.subscribe("stream:ftx:orders")
        channel = channels[0]
        while await channel.wait_message():
            json = await channel.get_json()
            market = json["data"]["symbol"]
            status = json["data"]["status"]
            date_str = json["date"]
            date = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S %Z").replace(
                tzinfo=timezone.utc
            )
            self.add_order(market, date, status)

    async def consume_mmstats(self):
        channels = await self.redis.subscribe("public:ftx:mmstats")
        channel = channels[0]
        while await channel.wait_message():
            json = await channel.get_json()
            data = json["data"]

            date_str = json["date"]
            date = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S %Z").replace(
                tzinfo=timezone.utc
            )

            for market_stat in data:
                market = market_stat["market"]
                deep_stat = market_stat["today_deep_pct"]
                bbo_stat = market_stat["today_bbo_pct"]
                self.add_mmstat(market, deep_stat, bbo_stat, date)

    async def send_to_telegram(self, msg):
        path = urljoin(TELEGRAM.base, TELEGRAM.path)
        params = TELEGRAM.get_params(msg)

        async with aiohttp.ClientSession() as session:
            async with session.request(
                "get", urljoin(TELEGRAM.base, path), params=params
            ) as resp:
                pass

    async def run(self):
        tasks = [
            self.consume_orders(),
            self.consume_mmstats(),
            self.schedule_checks(),
            self.schedule_stats_checks(),
            self.connection_check(),
        ]

        await asyncio.gather(*tasks)


async def main():
    state = State(2400, 600, 60)
    redis = await state.connect_redis()

    await state.run()
