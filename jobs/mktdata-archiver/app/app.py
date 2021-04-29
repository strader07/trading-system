import math
from datetime import datetime, date, timedelta

from mwzpyutil import Config, logger
from app.parquet import generate_parquet_files
from app.gcs import store_file
from app.utils import get_markets, RunSettings
from paf.tardis_client import booksbuilder


async def get_runs():
    config = Config()

    if config.archive_dates[0] == "yesterday":
        dates = [date.today() - timedelta(days=1)]
        all_markets = await get_markets(config, expiry=date.today())
        markets = [
            market
            for market in all_markets
            if market.enabled or market.expiry.date() >= dates[-1]
        ]

    else:
        all_markets = await get_markets(config)
        dates = sorted(
            [datetime.strptime(dt, "%Y-%m-%d").date() for dt in config.archive_dates]
        )
        markets = [
            market
            for market in all_markets
            if market.enabled or market.expiry.date() >= dates[-1]
        ]

    # Split across workers if workers_count > 1
    if config.workers_count > 1:
        markets.sort(key=lambda market: market.market)
        bucket_size = int(math.ceil(len(markets) / config.workers_count))
        start_index = config.worker_id * bucket_size

        if config.worker_id == config.workers_count - 1:
            end_index = len(markets)
        else:
            end_index = start_index + bucket_size

        logger.info(
            f"Worker: {config.worker_id+1}/{config.workers_count}. Processing {end_index-start_index} books."
        )
        markets = markets[start_index:end_index]

    if config.markets_filter[0] != "all":
        markets = [
            market for market in markets if market.instrument in config.markets_filter
        ]

    runs = []

    for dt_str in config.archive_dates:
        dt = (
            date.today() - timedelta(days=1)
            if dt_str == "yesterday"
            else datetime.strptime(dt_str, "%Y-%m-%d").date()
        )
        for market in markets:
            # TODO: check expiry and error if expired
            runs.append(RunSettings(dt, market, config.spot_exchanges))

    logger.info(f"Will run: {', '.join([str(setting) for setting in runs])}")
    return runs


async def get_book(settings):
    dt = [
        datetime.combine(settings.date, datetime.min.time()),
        datetime.combine(settings.date + timedelta(days=1), datetime.min.time()),
    ]
    orderbooks = await booksbuilder([settings.market], [dt], settings.spot_exchanges)
    return orderbooks


async def process_mktdata(runs):
    success = 0
    errors = 0

    for settings in runs:

        logger.info(f"Starting {settings} raw files generation.")

        if not settings.market.instrument:
            logger.warn(
                f"Warning: {settings.market.market} does not have a local instrument mapping."
            )
            logger.info("--")
            continue

        orderbooks = await get_book(settings)
        if len(orderbooks) != 1:
            logger.error(
                f"Error for {settings}: received invalid number of books: {len(orderbooks)}. Expected 1."
            )
            errors += 1
            logger.info("--")
            continue

        try:
            raw_files = await generate_parquet_files(
                list(orderbooks.values())[0], settings
            )
        except Exception as e:
            logger.error(f"Error generating raw files for {settings}")
            logger.error(e)
            errors += 1
            logger.info("--")
            continue
        else:
            logger.info(f"Generated raw files for {settings}")
            success += 1

        # try:
        #     for raw_file in raw_files:
        #         store_file(settings, raw_file)
        # except Exception as e:
        #     logger.error(f"Error uploading raw files for {settings}")
        #     logger.error(e)
        #     errors += 1
        #     logger.info("--")
        #     continue
        # else:
        #     logger.info(f"Successfully generated & uploaded raw files for {settings}")
        #     success += 1

        logger.info("--")

    logger.info("========================================================")
    logger.info(f"summary: success={success} errors={errors}")
    logger.info("========================================================")

    if errors > 0:
        exit(1)


async def main():
    runs = await get_runs()
    await process_mktdata(runs)
