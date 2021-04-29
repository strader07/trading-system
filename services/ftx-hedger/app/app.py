import asyncio
from decimal import Decimal, getcontext

from mwzpyutil import Config, connect_redis, logger
from ftx_client.api import FTXData, market_to_instrument


def verify_request(data):
    if b"symbol" not in data:
        logger.error(f"Error! Symbol not found in invalid stream format for {data}")
        return False

    if b"size" not in data:
        logger.error(f"Error! Size not found in invalid stream format for {data}")
        return False

    if b"size" not in data:
        logger.error(f"Error! size not found in invalid stream format for {data}")
        return False

    if b"subaccount" not in data:
        logger.error(f"Error! Subaccount not found in invalid stream format for {data}")
        return False

    return True


async def get_position(ftx_data, ftx_symbol, subaccount):
    pos = await ftx_data.get_position(ftx_symbol, subaccount)

    if not pos:
        return Decimal(0), Decimal(0)

    price = Decimal(pos["avg_price"])
    market_size = Decimal(pos["net_size"])
    return price, market_size


async def execute_hedge(ftx_data, instrument, size, ftx_symbol, subaccount):
    try:
        price, market_size = await get_position(ftx_data, ftx_symbol, subaccount)
    except Exception as e:
        logger.error(f"Error in retrieving {ftx_symbol} position: {e}")
        return False

    notional = price * market_size
    if notional > Decimal(5000):
        logger.warning(
            f"Skipping hedge {instrument} for {market_size}. Notional above $5,000. Size={size}. Notional={notional}"
        )
        return False

    logger.debug(f"Hedging {instrument} for {size}")

    if size == 0:
        return
    elif size > 0:
        side = "buy"
    if size < 0:
        side = "sell"

    order = await ftx_data.place_order(
        subaccount, ftx_symbol, side, None, abs(float(size)), "market", ioc=True,
    )

    if not order:
        logger.error("Error placing order.")
        return False

    logger.info(f"Hedged {instrument} {float(size)} {side}")
    return True


async def process_xread(ftx_data, instrument, size, side, subaccount, market):
    logger.debug(f"Got {instrument} {size} {side} {subaccount}")

    size *= 1 if side == "buy" else -1
    success = await execute_hedge(ftx_data, instrument, size, market, subaccount)

    if not success:
        logger.error(
            f"Error while hedging {instrument} {side} {size} {subaccount}, retrying in 60 seconds."
        )

        async def rerun():
            await asyncio.sleep(60)
            success = await execute_hedge(
                ftx_data, instrument, size, market, subaccount
            )
            if not success:
                logger.error(
                    f"Error hedging after second try. Hedge: {instrument} {side} {size} {subaccount}"
                )

        await asyncio.ensure_future(rerun())

    return True


async def xread(ftx_data, exp_redis):
    last_id = await exp_redis.get("hedge-request-last-id")
    last_id = last_id.decode() if last_id else str("0-0")
    logger.info(f"Subscribing to hedge-request starting from {last_id}")

    resp = await exp_redis.xread(["hedge-request"], latest_ids=[last_id])

    while True:
        logger.debug(resp)

        for r in resp:
            stream = r[0]
            request_id = r[1]
            data = r[2]

            if not verify_request(data):
                continue

            logger.info(f"Processing {request_id}")

            instrument = data[b"symbol"].decode()
            size = Decimal(data[b"size"].decode())
            side = data[b"side"].decode()
            subaccount = data[b"subaccount"].decode()
            logger.debug(f"Got {instrument} {size} {side} {subaccount}")

            market = await exp_redis.hget(f"ftx:{instrument}", "market")
            if not market:
                logger.error(f"Received request for an unknown instrument: {instrument}")
                continue

            getcontext().prec = 9

            await process_xread(
                ftx_data, instrument, size, side, subaccount, market.decode(),
            )

            await exp_redis.set("hedge-request-last-id", request_id)
            last_id = request_id
            logger.debug("================================================")

        logger.debug(f"Reading from {last_id}")
        resp = await exp_redis.xread(["hedge-request"], latest_ids=[last_id])


async def main():
    config = Config()
    exp_redis = await connect_redis(config.exposed_redis, "exposed_redis")
    ftx_data = FTXData(
        config.key,
        config.secret,
        config.subaccounts,
        config.subaccounts_markets,
        config.ticker_markets,
        config.trades_markets,
    )
    tasks = [xread(ftx_data, exp_redis)]
    await asyncio.gather(*tasks)
