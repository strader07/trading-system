import asyncio
import logging
import re
import calendar
import math
from datetime import datetime, timezone, date
from typing import List

from ftx_client.client import FtxClient, WSChannel
from ftx_client.mappings import mappings
from ftx_client.classes import MMStats
from mwzpyutil.types import (
    Ticker,
    Trade,
    Candle,
    MarketType,
    Market,
    Fill,
    RunningFill,
)

import pendulum


def roundnum(num, dp=2):
    if not num:
        return 0
    return round(num, dp)


def count_dp(num):
    if "." not in num:
        return 0
    else:
        return str(num)[::-1].find(".")


def market_to_instrument(market):
    for ftx_mapping, mwz_mapping in mappings.items():
        if ftx_mapping in market:
            return market.replace(ftx_mapping, mwz_mapping)
    return ""


class FTXData:
    key = None
    secret = None
    subaccounts = None
    markets = None

    on_order_cb = None
    on_ticker_cb = None
    on_trade_cb = None
    on_raw_trade_cb = None
    on_book_cb = None
    on_fill_cb = None

    # cache
    orders = {}
    clients = {}
    market_running_fills = {}

    def __init__(
        self,
        key,
        secret,
        subaccounts,
        subaccounts_markets,
        ticker_markets=None,
        trades_markets=None,
        book_markets=None,
    ):
        self.key = key
        self.secret = secret
        self.subaccounts = subaccounts
        self.subaccounts_markets = subaccounts_markets
        self.ticker_markets = ticker_markets if ticker_markets else []
        self.trades_markets = trades_markets if trades_markets else []
        self.book_markets = book_markets if book_markets else []

        for subaccount in self.subaccounts:
            self.clients[subaccount] = FtxClient(self.key, self.secret, subaccount)
        self.clients[""] = FtxClient(self.key, self.secret)  # rename to main?

    def set_historical_mode(self, from_date, to_date):
        self.clients[""].set_historical_mode(from_date, to_date)

    async def place_order(self, subaccount, *args, **kwargs):
        return await self.clients[subaccount].place_order(*args, **kwargs)

    def market_making_size(self, market):
        if market.startswith("BTC"):
            return 20000
        elif market.startswith("ETH"):
            return 7500
        elif market.startswith("EOS"):
            return 7500
        elif market.startswith("XRP"):
            return 7500
        else:
            return 4000

    async def _get_markets(self, func, market_filter=None):
        if not market_filter:
            market_filter = lambda _: True
        markets = []

        account = await self.clients[""].get_account_info(suppress=True)
        maker_fee = float(account["makerFee"]) if account else -1
        taker_fee = float(account["takerFee"]) if account else -1

        resp = await func()
        for market in resp:
            tick_size = (
                "{:.8f}".format(market["priceIncrement"]).rstrip("0").rstrip(".")
            )
            min_size = "{:.8f}".format(market["sizeIncrement"]).rstrip("0").rstrip(".")

            our_market = Market(
                exchange="ftx",
                market=market["name"],
                instrument=market_to_instrument(market["name"]),
                type_=MarketType[market["type"]],
                enabled=market["enabled"],
                maker_fee=maker_fee,
                taker_fee=taker_fee,
                tick_size=tick_size,
                min_size=min_size,
                price_precision=count_dp(tick_size),
                size_precision=count_dp(min_size),
                mm_size=self.market_making_size(market["name"]),
                expiry=(
                    pendulum.parse(market["expiry"]).replace(tzinfo=None)
                    if "expiry" in market and market["expiry"]
                    else None
                ),
            )

            if not market_filter(our_market):
                continue

            markets.append(our_market)

        return markets

    async def get_markets(self):
        # We only care about futures and perpetuals right now.
        filt = lambda market: market.type_ in (MarketType.perpetual, MarketType.future)
        return await self._get_markets(self.clients[""].get_futures, filt)

    async def get_futures(self):
        filt = lambda market: market.type_ == MarketType.future
        return await self._get_markets(self.clients[""].get_futures, filt)

    async def get_expired_futures(self, expiry_date: date = None):
        filt = lambda market: market.type_ == MarketType.future and (
            market.expiry.date() == expiry_date if expiry_date else True
        )
        return await self._get_markets(self.clients[""].get_expired_futures, filt)

    async def get_trades(self, market, limit=20) -> List[Trade]:
        trades = []
        http_trades = await self.clients[""].get_trades(market, limit) or []
        for tdata in http_trades:
            trades.append(
                Trade(
                    market=market,
                    id=int(tdata["id"]),
                    time=datetime.strptime(tdata["time"], "%Y-%m-%dT%H:%M:%S.%f%z"),
                    price=float(tdata["price"]),
                    size=float(tdata["size"]),
                    side=tdata["side"],
                    liquidation=True if tdata["liquidation"] == "true" else False,
                )
            )
        return trades

    async def get_historical_data(
        self,
        market: str,
        resolution: int,
        limit: int,
        start_time: datetime = None,
        end_time: datetime = None,
    ) -> List[Candle]:

        resp = (
            await self.clients[""].get_candles(
                market,
                resolution,
                limit=limit,
                start_time=start_time,
                end_time=end_time,
            )
            or []
        )

        candles = []
        for candle in resp:
            candles.append(
                Candle(
                    open_=candle["open"],
                    close=candle["close"],
                    high=candle["high"],
                    low=candle["low"],
                    volume=candle["volume"],
                    startTime=candle["startTime"],
                    time=int(candle["time"]),
                )
            )
        return candles

    async def get_wallets(self):
        all_wallets = []
        resp = await self.clients[""].get_all_balances()
        for subaccount, wallets in resp.items():
            for wallet in wallets:
                try:
                    if wallet["total"] != 0:
                        wal = {}
                        wal["coin"] = wallet["coin"]
                        wal["free"] = roundnum(wallet["free"])
                        wal["total"] = roundnum(wallet["total"])
                        wal["usd_value"] = roundnum(wallet["usdValue"])
                        wal["subaccount"] = subaccount
                        all_wallets.extend([wal])
                except:
                    logging.error(f"Error in FTX wallets response: {wallet}")
                    continue
        return all_wallets

    async def get_position(self, market, subaccount):
        client = self.clients[subaccount]
        position = await client.get_position(market, show_avg_price=True)

        if not position:
            return {}

        pos = {}
        pos["symbol"] = position["future"]
        pos["entry_price"] = roundnum(position["entryPrice"], 5)
        pos["net_size"] = position["netSize"]
        pos["open_size"] = position["openSize"]
        pos["cost"] = roundnum(position["cost"], 5)
        pos["side"] = position["side"]
        pos["est_liq_price"] = roundnum(position["estimatedLiquidationPrice"])
        recent_pnl = position.get("recentPnl")
        recent_pnl = roundnum(recent_pnl) if recent_pnl else None
        pos["recent_pnl"] = recent_pnl
        pos["unrealized_pnl"] = roundnum(position["unrealizedPnl"])
        pos["realized_pnl"] = roundnum(position["realizedPnl"])
        pos["subaccount"] = subaccount
        pos["instrument"] = market_to_instrument(position["future"])
        pos["avg_price"] = roundnum(position["recentAverageOpenPrice"], 5)
        pos["break_even_price"] = roundnum(position["recentBreakEvenPrice"], 5)
        # avg_price = pos["entry_price"]
        # if position["future"] in self.market_running_fills:
        #     avg_price = self.market_running_fills[position["future"]].avg_price()
        return pos

    async def get_positions(self):
        all_positions = []
        for subaccount in self.subaccounts:
            client = self.clients[subaccount]

            subaccount_positions = await client.get_positions(show_avg_price=True) or []
            for position in subaccount_positions:
                if position["netSize"] != 0:
                    try:
                        pos = {}
                        pos["symbol"] = position["future"]
                        pos["entry_price"] = roundnum(position["entryPrice"], 5)
                        pos["net_size"] = position["netSize"]
                        pos["open_size"] = position["openSize"]
                        pos["cost"] = roundnum(position["cost"], 5)
                        pos["side"] = position["side"]
                        pos["est_liq_price"] = roundnum(
                            position["estimatedLiquidationPrice"]
                        )
                        recent_pnl = position.get("recentPnl")
                        recent_pnl = roundnum(recent_pnl) if recent_pnl else None
                        pos["recent_pnl"] = recent_pnl
                        pos["unrealized_pnl"] = roundnum(position["unrealizedPnl"])
                        pos["realized_pnl"] = roundnum(position["realizedPnl"])
                        pos["subaccount"] = subaccount
                        pos["instrument"] = market_to_instrument(position["future"])

                        pos["break_even_price"] = roundnum(
                            position["recentBreakEvenPrice"], 5
                        )

                        # if position["future"] in self.market_running_fills:
                        #     avg_price = self.market_running_fills[
                        #         position["future"]
                        #     ].avg_price()
                        pos["avg_price"] = roundnum(
                            position["recentAverageOpenPrice"], 5
                        )
                    except Exception as e:
                        logging.error(f"Error in FTX positions response: {position}")
                        logging.error(f"Exception: {e}")
                        continue

                    # collateralUsed
                    # recentBreakEvenPrice
                    all_positions.extend([pos])

        all_positions = sorted(
            all_positions, key=lambda i: (i["symbol"], i["subaccount"])
        )
        return all_positions

    async def get_mm_stats(self):
        tradedate = datetime.now(timezone.utc)

        market_stats = {}

        for subaccount in self.subaccounts:
            if not subaccount:
                continue

            client = self.clients[subaccount]
            subaccount_markets = self.subaccounts_markets[subaccount]

            month_stats = await client.get_all_month_market_making_stats() or []
            day_stats = await client.get_all_market_making_stats() or []

            for stat in month_stats:
                if stat["market"] not in subaccount_markets:
                    continue
                try:
                    market = stat["market"]
                    bbo = stat["atBboFracPassed"]
                    deep = stat["nearBboFracPassed"]

                    if market not in market_stats:
                        market_stats[market] = MMStats(market)
                    market_stats[market].add_month_stat(bbo, deep, subaccount)
                except KeyError as e:
                    logging.error(f"Error retrieving mmstats for stat: {stat}: {e}")

            for stat in day_stats:
                if stat["market"] not in subaccount_markets:
                    continue
                try:
                    date = datetime.strptime(stat["date"], "%a, %d %b %Y %X %Z")
                    if date.date() != tradedate.date():
                        continue
                    if market not in market_stats:
                        market_stats[market] = MMStats(market)
                    market = stat["market"]
                    bbo = stat["atBboFractionPassed"]
                    deep = stat["nearBboFractionPassed"]
                    market_stats[market].add_today_stat(bbo, deep, subaccount)
                except KeyError as e:
                    logging.error(f"Error retrieving mmstats for stat: {stat}: {e}")

        tradedate_str = tradedate.strftime("%d/%m/%Y")

        month_range = calendar.monthrange(tradedate.year, tradedate.month)
        rem_days = (month_range[1] - tradedate.day) or 1
        month_deep_target_snaps = (month_range[1] * 48) * 0.50
        month_bbo_target_snaps = (month_range[1] * 48) * 0.15

        real_month_deep_target_snaps = month_deep_target_snaps
        real_month_bbo_target_snaps = month_bbo_target_snaps

        month_deep_target_snaps += 10
        month_bbo_target_snaps += 5

        all_mm_stats = []
        for key, stat in market_stats.items():
            today = stat.today_stats
            month = stat.month_stats

            day_deep_target = int(
                math.ceil((month_deep_target_snaps - month.deep_snaps) / rem_days)
            )
            day_bbo_target = int(
                math.ceil((month_bbo_target_snaps - month.bbo_snaps) / rem_days)
            )
            if day_deep_target < 0:
                day_deep_target = 0
            if day_bbo_target < 0:
                day_bbo_target = 0

            ui_deep_target = int(
                math.ceil((real_month_deep_target_snaps - month.deep_snaps) / rem_days)
            )
            ui_bbo_target = int(
                math.ceil((real_month_bbo_target_snaps - month.bbo_snaps) / rem_days)
            )
            if ui_deep_target < 0:
                ui_deep_target = 0
            if ui_bbo_target < 0:
                ui_bbo_target = 0

            all_mm_stats.append(
                {
                    "date": tradedate_str,
                    "market": stat.market,
                    "today_deep_pct": roundnum(today.deep_pct, 4),
                    "today_bbo_pct": roundnum(today.bbo_pct, 4),
                    "today_deep_snaps": roundnum(today.deep_snaps),
                    "today_bbo_snaps": roundnum(today.bbo_snaps),
                    "month_deep_pct": roundnum(month.deep_pct, 4),
                    "month_bbo_pct": roundnum(month.bbo_pct, 4),
                    "month_deep_snaps": roundnum(month.deep_snaps),
                    "month_bbo_snaps": int(math.ceil(month.bbo_snaps)),
                    "day_deep_target": day_deep_target,
                    "day_bbo_target": day_bbo_target,
                    "ui_deep_target": ui_deep_target,
                    "ui_bbo_target": ui_bbo_target,
                    "subaccount": ",".join(stat.subaccounts),
                }
            )

        return all_mm_stats

    async def get_account_info(self):
        account_info = {}
        account_info["breakdown"] = []

        all_account_value = 0
        all_position_size = 0
        all_collateral = 0
        all_free_collateral = 0
        all_pnl = 0
        all_today_pnl = 0

        for subaccount in self.subaccounts:
            client = self.clients[subaccount]

            subaccount_info = await client.get_account_info()
            subaccount_pnl = await client.get_pnl()

            try:
                account_value = subaccount_info["totalAccountValue"]
                position_size = subaccount_info["totalPositionSize"]
                collateral = subaccount_info["collateral"]
                free_collateral = subaccount_info["freeCollateral"]
            except:
                logging.error(f"Error in FTX account info: {subaccount_info}")
                continue

            today_pnl = 0
            today = str(subaccount_pnl["today"])
            if today in subaccount_pnl["pnlByDay"]:
                today_pnl = sum(
                    [v for _, v in subaccount_pnl["pnlByDay"][today].items()]
                )
            pnl = sum(
                [
                    v
                    for _, v in subaccount_pnl["totalPnl"].items()
                    if isinstance(v, float)
                ]
            )

            account_info["breakdown"].append(
                {
                    "subaccount": subaccount if subaccount else "Main",
                    "account_value": roundnum(account_value),
                    "position_size": roundnum(position_size),
                    "collateral": roundnum(collateral),
                    "free_collateral": roundnum(free_collateral),
                    "today_pnl": roundnum(today_pnl),
                    "pnl": roundnum(pnl),
                    "status": "",
                }
            )

            all_account_value += account_value
            all_position_size += position_size
            all_collateral += collateral
            all_free_collateral += free_collateral
            all_today_pnl += today_pnl
            all_pnl += pnl

            all_account_info = {}
            all_account_info["account_value"] = roundnum(all_account_value)
            all_account_info["position_size"] = roundnum(all_position_size, 4)
            all_account_info["collateral"] = roundnum(all_collateral)
            all_account_info["free_collateral"] = roundnum(all_free_collateral)
            all_account_info["today_pnl"] = roundnum(all_today_pnl)
            all_account_info["pnl"] = roundnum(all_pnl)

            account_info["all"] = all_account_info

        return account_info

    async def snapshot_open_orders(self):
        orders = {}

        for subaccount in self.subaccounts:
            client = self.clients[subaccount]
            subaccount_orders = await client.get_open_orders()

            for order in subaccount_orders:
                ord = {}
                ord["id"] = order["id"]
                ord["symbol"] = order["market"]
                ord["price"] = order["price"]
                ord["size"] = order["size"]
                ord["remaining_size"] = order["remainingSize"]
                ord["filled_size"] = order["filledSize"]
                ord["avg_fill_price"] = order["avgFillPrice"]
                ord["side"] = order["side"]
                ord["type"] = order["type"]
                ord["status"] = order["status"]
                ord["clOrdID"] = order["clientId"]

                orders[ord["id"]] = ord

        self.orders = orders

    def register_on_order(self, cb):
        self.on_order_cb = cb

    def register_on_ticker(self, cb):
        self.on_ticker_cb = cb

    def register_on_trade(self, cb):
        self.on_trade_cb = cb

    def register_on_raw_trade(self, cb):
        self.on_raw_trade_cb = cb

    def register_on_book(self, cb):
        self.on_book_cb = cb

    def register_on_fill(self, cb):
        self.on_fill_cb = cb

    async def on_order(self, msg):
        data = msg["data"]
        new_order = {
            "id": data["id"],
            "symbol": data["market"],
            "instrument": market_to_instrument(data["market"]),
            "price": data["price"],
            "size": data["size"],
            "remaining_size": data["remainingSize"],
            "filled_size": data["filledSize"],
            "avg_fill_price": data["avgFillPrice"],
            "side": data["side"],
            "type": data["type"],
            "status": data["status"],
            "clOrdID": data["clientId"],
        }

        oid = data["id"]
        if new_order["status"] == "new":
            self.orders[oid] = new_order
        elif new_order["status"] == "closed":
            if oid in self.orders:
                del self.orders[oid]
        else:
            self.orders[oid] = new_order

        ords = [order for _, order in self.orders.items()]
        ords = sorted(ords, key=lambda o: o["symbol"])
        if self.on_order_cb:
            await self.on_order_cb(ords, new_order)

    async def on_ticker(self, msg):
        data = msg["data"]
        ticker = Ticker(
            market=msg["market"],
            bid_px=float(data["bid"]),
            bid_qty=float(data["bidSize"]),
            ask_px=float(data["ask"]),
            ask_qty=float(data["askSize"]),
            last=float(data["last"]),
            time=data["time"],
        )
        if self.on_ticker_cb:
            await self.on_ticker_cb(ticker, ticker.market)

    async def on_trade(self, msg):
        if self.on_raw_trade_cb:
            await self.on_raw_trade_cb(msg)

        if self.on_trade_cb:
            data = msg["data"]
            trades = []
            for tdata in data:
                trades.append(
                    Trade(
                        market=msg["market"],
                        id=int(tdata["id"]),
                        time=datetime.strptime(tdata["time"], "%Y-%m-%dT%H:%M:%S.%f%z"),
                        price=float(tdata["price"]),
                        size=float(tdata["size"]),
                        side=tdata["side"],
                        liquidation=True if tdata["liquidation"] == "true" else False,
                    )
                )

            await self.on_trade_cb(trades, msg["market"])

    async def on_book(self, msg):
        # TODO: change/add to internal structures?
        if self.on_book_cb:
            await self.on_book_cb(msg)

    async def on_fill(self, msg):
        data = msg["data"]
        fill = Fill(
            id_=data["id"],
            market=data["future"],
            order_id=int(data["orderId"]),
            price=float(data["price"]),
            size=float(data["size"]),
            side=data["side"],
            fee=float(data["fee"]),
            fee_rate=float(data["feeRate"]),
            liquidity=data["liquidity"],
            time=data["time"],
        )
        if fill.market in self.market_running_fills:
            running_fill = self.market_running_fills[fill.market]
            running_fill.add_fill(fill.price, fill.size, fill.side)
            if running_fill.total_size == 0:
                del self.market_running_fills[fill.market]
        else:
            running_fill = RunningFill(0, 0)
            running_fill.add_fill(fill.price, fill.size, fill.side)
            self.market_running_fills[fill.market] = running_fill

        if self.on_fill_cb:
            await self.on_fill_cb(fill)

    def subscribe_ws(self):
        tasks = []
        public_channels = []
        private_channels = []

        # Public channels
        ticker_channels = [
            WSChannel("ticker", self.on_ticker, market)
            for market in self.ticker_markets
        ]
        trades_channels = [
            WSChannel("trades", self.on_trade, market) for market in self.trades_markets
        ]
        book_channels = [
            WSChannel("orderbook", self.on_book, market) for market in self.book_markets
        ]
        public_channels = ticker_channels + trades_channels + book_channels
        tasks.append(asyncio.Task(self.clients[""].subscribe_ws(public_channels)))

        # Private channels
        for subaccount in self.subaccounts:
            if not subaccount:
                continue
            client = self.clients[subaccount]
            private_channels = [
                WSChannel(
                    "orders", self.on_order, on_reconnect=self.snapshot_open_orders
                ),
                WSChannel("fills", self.on_fill),
            ]
            tasks.append(asyncio.Task(client.subscribe_ws(private_channels)))

        return tasks

    async def subscribe_book(self):
        if not (self.trades_markets or self.book_markets):
            raise ValueError(
                f"At least one of trades or book markets must be specified to subscribe to the book."
            )

        trades_channels = (
            [
                WSChannel("trades", self.on_trade, market)
                for market in self.trades_markets
            ]
            if self.trades_markets
            else []
        )

        book_channels = (
            [
                WSChannel("orderbook", self.on_book, market)
                for market in self.book_markets
            ]
            if self.book_markets
            else []
        )

        await self.clients[""].subscribe_ws(trades_channels + book_channels)

    async def subscribe_http_book(self):
        if not (self.trades_markets or self.book_markets):
            raise ValueError(
                f"At least one of trades or book markets must be specified to subscribe to the book."
            )

        trades_channels = (
            [
                WSChannel("trades", self.on_trade, market)
                for market in self.trades_markets
            ]
            if self.trades_markets
            else []
        )

        book_channels = (
            [
                WSChannel("orderbook", self.on_book, market)
                for market in self.book_markets
            ]
            if self.book_markets
            else []
        )

        await self.clients[""].subscribe_http(trades_channels + book_channels)
