import asyncio
import datetime
import json
from functools import partial
from typing import Any, List
from dataclasses import dataclass
from enum import Enum

from ftx_client.api import FTXData, market_to_instrument
from mwzpyutil import Config, connect_redis, logger


def now_tz_str():
    local_timezone = (
        datetime.datetime.now(datetime.timezone(datetime.timedelta(0)))
        .astimezone()
        .tzinfo
    )
    nowtz = datetime.datetime.now().replace(tzinfo=local_timezone)
    return nowtz.strftime("%d/%m/%Y %H:%M:%S %Z")


@dataclass
class OnPoll:
    redis: Any
    channel: str
    cb: Any


class SchedType(Enum):
    INTERVAL = 0
    TIME = 1


@dataclass
class CallbackSchedule:
    type: SchedType
    interval: int = 0
    time: datetime.time = None


# TODO: BAD!! Replace this.
# Call the cb function at first ALWAYS with a flag saying its an initial run
# Then subsequent runs in the while loop do not pass it. That way you can differentiate.
intraday_run = True


async def poll(func, schedule, on_polls: List[OnPoll], *args, **kwargs):
    if schedule.type is SchedType.INTERVAL:
        for o in on_polls:
            logger.info(
                f"Poll publishing to {o.channel} every {schedule.interval} seconds"
            )

        while True:
            data = await func(*args, **kwargs)
            for o in on_polls:
                await o.cb(o, data)

            if schedule.interval == 0:
                return
            await asyncio.sleep(schedule.interval)

    else:
        for o in on_polls:
            logger.info(f"Poll publishing to {o.channel} scheduled at {schedule.time}")

        while True:
            data = await func(*args, **kwargs)
            for o in on_polls:
                await o.cb(o, data)

            now = datetime.datetime.now(datetime.timezone.utc)
            time_val = schedule.time

            next_run = now + datetime.timedelta(days=1)
            next_run = next_run.replace(
                hour=schedule.time.hour,
                minute=schedule.time.minute,
                second=schedule.time.second,
                microsecond=schedule.time.microsecond,
            )
            for o in on_polls:
                logger.info(f"Poll publishing to {o.channel} next at {next_run}")
            await asyncio.sleep(
                (next_run - datetime.datetime.now(datetime.timezone.utc)).seconds
            )


async def on_poll(on_poll, data):
    dtstr = now_tz_str()
    payload = {"data": data, "date": dtstr}
    logger.debug(f"Poll publishing on {on_poll.channel} payload: {payload}")
    await on_poll.redis.publish_json(on_poll.channel, payload)


async def on_sorted_set(on_poll, data):
    key = on_poll.channel
    for d in data:
        logger.debug(
            f"Poll updating sorted set {key} with score: {d.score()} and payload: {d}"
        )
        await on_poll.redis.zadd(key, d.score(), str(d))


async def on_markets(on_poll, markets):
    global intraday_run

    if intraday_run:
        logger.info("Intraday run, not resetting clOrdID.")

    for market in markets:
        key = on_poll.channel.format(instrument=market.instrument)

        instrument_data = {
            "market": market.market,
            "instrument": market.instrument,
            "type": market.type_.name,
            "enabled": int(market.enabled),
            "maker_fee": market.maker_fee,
            "taker_fee": market.taker_fee,
            "tick_size": market.tick_size,
            "min_size": market.min_size,
            "price_precision": market.price_precision,
            "size_precision": market.size_precision,
            "mm_size": market.mm_size,
        }

        if not market.instrument:
            logger.warn(f"Unhandled FTX symbol: {market.market}")

        # We only restart clOrdId on EOD restart of dropcopy.
        if not intraday_run:
            instrument_data["clOrdID"] = 0
            logger.info(f"Resetting {market.instrument} clOrdID to 0.")

        # Check clordid existence, if nothing exists, reset to 0.
        clOrdID_res = await on_poll.redis.hmget(key, "clOrdID")
        clOrdID = clOrdID_res[0]
        if clOrdID is None:
            instrument_data["clOrdID"] = 0
            logger.info(f"clOrdID for {market.instrument} not found. Setting to 0.")

        logger.debug(f"Poll updating dict {key} with keys: {instrument_data}")
        await on_poll.redis.hmset_dict(key, instrument_data)

    intraday_run = False


async def on_position_rhash(on_poll, data):
    key = on_poll.channel
    dtstr = now_tz_str()
    payload = {"data": data, "date": dtstr}
    logger.debug(f"Poll publishing on {key} payload: {payload}")
    await on_poll.redis.set(key, json.dumps(payload))


async def on_cpp_positions(on_poll, positions):
    key_fmt = on_poll.channel

    instruments_with_positions = [position["instrument"] for position in positions]
    key_pattern = "ftx:positions:"
    positions_keys = await on_poll.redis.keys(f"{key_pattern}*")
    for position_key in positions_keys:
        key = position_key[len(key_pattern) :].decode()
        if key not in instruments_with_positions:
            logger.debug(f"Deleting {position_key}, no positions.")
            await on_poll.redis.delete(position_key)

    for position in positions:
        key = key_fmt.format(instrument=position["instrument"])
        position_data = {
            "size": abs(position["net_size"]),
            "side": position["side"],
            "avg_px": position["avg_price"],
        }
        logger.debug(f"Poll publishing on {key} payload: {position_data}")
        await on_poll.redis.hmset_dict(key, position_data)


async def on_cpp_mmstats(on_poll, data):
    # p2f = lambda x: float(x.strip("%")) / 100
    logger.debug(data)
    for d in data:
        instrument = market_to_instrument(d["market"])
        full_chan = on_poll.channel.format(instrument=instrument)
        if instrument:
            month_bbo_pct = d["month_bbo_pct"]
            month_deep_pct = d["month_deep_pct"]
            payload = f"{month_bbo_pct},{month_deep_pct}"

        logger.debug(f"Poll publishing on {full_chan} payload: {payload}")
        await on_poll.redis.publish_json(full_chan, payload)


async def on_order(redis, exp_redis, channel, stream_channel, all_orders, order_update):
    dtstr = now_tz_str()
    payload = {"data": all_orders, "date": dtstr}
    logger.debug(f"Stream publishing on {channel} payload: {payload}")
    await redis.publish_json(channel, payload)
    if order_update.get("clOrdID"):
        current_last_clordid = await exp_redis.hmget(
            f"ftx:{order_update['instrument']}", "clOrdID"
        )
        if int(order_update["clOrdID"]) > int(current_last_clordid[0]):
            await exp_redis.hmset(
                f"ftx:{order_update['instrument']}",
                "clOrdID",
                int(order_update["clOrdID"]),
            )

    if stream_channel:
        stream_payload = {"data": order_update, "date": dtstr}
        logger.debug(f"Stream publishing on {stream_channel} payload: {stream_payload}")
        await redis.publish_json(stream_channel, stream_payload)

    # if snapshot_key:
    #     await redis.set(snapshot_key, json.dumps(payload))


async def on_ticker(redis, base_channel, data, market):
    channel = f"{base_channel}:{market}"
    payload = str(data)
    await redis.publish(channel, payload)


async def on_trade(redis, base_channel, data, market):
    instrument = market_to_instrument(market)
    channel = f"{base_channel}:{instrument}"
    # logger.debug(f"Publishing to {channel}: {data}")

    for trade in data:
        message_id = f"{int(trade.time.timestamp()*1000)}-{trade.id}"
        logger.debug(f"Publishing {message_id} to {channel} date: {trade.time}")
        try:
            await redis.xadd(
                channel,
                {
                    "price": round(trade.price, 8),
                    "size": round(trade.size, 8),
                    "side": trade.side,
                },
                message_id=message_id.encode(),
                max_len=40,
            )
        except:
            pass


async def on_fill(redis, channel, data):
    dtstr = now_tz_str()
    payload = {"data": data.to_dict(), "date": dtstr}
    logger.debug(f"Stream publishing on {channel} payload: {payload}")
    await redis.publish_json(channel, payload)


def setup_subscribe_orders(redis, exp_redis, ftx_data):
    # Disable snapshot orders hash
    orders_channels = ["public:ftx:orders", "stream:ftx:orders"]
    on_order_partial = partial(
        on_order, redis, exp_redis, orders_channels[0], orders_channels[1]
    )
    ftx_data.register_on_order(on_order_partial)
    for chan in orders_channels:
        logger.info(f"Stream publishing to {chan}")


def setup_subscribe_ticker(redis, ftx_data, markets):
    base_channel = "stream:ftx:ticker"
    on_ticker_partial = partial(on_ticker, redis, base_channel)
    ftx_data.register_on_ticker(on_ticker_partial)
    for market in markets:
        logger.info(f"Stream publishing to base {base_channel}:{market}")


async def setup_subscribe_trades(redis, ftx_data, markets):
    base_channel = "stream:ftx:trades"
    on_trade_partial = partial(on_trade, redis, base_channel)
    ftx_data.register_on_trade(on_trade_partial)

    for market in markets:
        instrument = market_to_instrument(market)
        logger.info(f"Stream publishing to base {base_channel}:{instrument}")
        bootstrap_trades = await ftx_data.get_trades(market, 40)
        bootstrap_trades.reverse()
        await on_trade_partial(bootstrap_trades, market)
        logger.info(f"Bootstrapped stream {base_channel}:{instrument}")


def setup_subscribe_fills(redis, ftx_data):
    channel = "stream:ftx:fills"
    on_fill_partial = partial(on_fill, redis, channel)
    ftx_data.register_on_fill(on_fill_partial)
    logger.info(f"Stream publishing to base {channel}")


async def startFTX(redis, exp_redis, ftx_data, candle_markets, trades_markets):
    setup_subscribe_orders(redis, exp_redis, ftx_data)
    # setup_subscribe_ticker(redis, ftx_data)
    setup_subscribe_fills(redis, ftx_data)
    await setup_subscribe_trades(exp_redis, ftx_data, trades_markets)

    tasks = [
        poll(
            ftx_data.get_markets,
            CallbackSchedule(SchedType.TIME, time=datetime.time(0, 5, 0, 0)),
            [OnPoll(exp_redis, "ftx:{instrument}", on_markets)],
        ),
        poll(
            ftx_data.get_wallets,
            CallbackSchedule(SchedType.INTERVAL, interval=5),
            [OnPoll(redis, "public:ftx:wallets", on_poll)],
        ),
        poll(
            ftx_data.get_positions,
            CallbackSchedule(SchedType.INTERVAL, interval=4),
            [
                OnPoll(redis, "public:ftx:positions", on_poll),
                OnPoll(redis, "ftx:positions", on_position_rhash),
                OnPoll(exp_redis, "ftx:positions:{instrument}", on_cpp_positions),
            ],
        ),
        poll(
            ftx_data.get_mm_stats,
            CallbackSchedule(SchedType.INTERVAL, interval=32),
            [
                OnPoll(redis, "public:ftx:mmstats", on_poll),
                OnPoll(exp_redis, "stream:ftx:mmstats:{instrument}", on_cpp_mmstats),
            ],
        ),
        poll(
            ftx_data.get_account_info,
            CallbackSchedule(SchedType.INTERVAL, interval=9),
            [OnPoll(redis, "public:ftx:accountinfo", on_poll)],
        ),
        *ftx_data.subscribe_ws(),
    ]

    # for market in candle_markets:
    #     tasks.append(
    #         poll(
    #             ftx_data.get_historical_data,
    #             CallbackSchedule(SchedType.TIME, time=datetime.time(0, 5, 0, 0)),
    #             [OnPoll(exp_redis, f"ftx:md:{market}:daily", on_sorted_set)],
    #             market,
    #             86400,
    #             3,
    #         ),
    #     )

    await asyncio.gather(*tasks)

    logger.info("cleaning up startFTX")  # this is never reached, fix
    redis.close()
    await redis.wait_closed()


async def main():
    config = Config()
    redis = await connect_redis(config.redis, "private")
    exp_redis = await connect_redis(config.exposed_redis, "exposed")
    ftx_data = FTXData(
        config.key,
        config.secret,
        config.subaccounts,
        config.subaccounts_markets,
        config.ticker_markets,
        config.trades_markets,
    )
    await asyncio.gather(
        startFTX(
            redis, exp_redis, ftx_data, config.ticker_markets, config.trades_markets
        )
    )
