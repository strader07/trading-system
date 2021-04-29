import os
import sys
import logging
import aioredis
from mwzpyutil.classes import RedisConfig

os.environ['LOG_LEVEL']='DEBUG'
os.environ['FTXKEY']=''
os.environ['FTXSECRET']=''
os.environ['COREPACK_FAMILIES']=''
# Change the ones below
os.environ['EXCHANGES']='gateio'
os.environ['SPOT_EXCHANGES']='gateio'
os.environ['MARKETS_FILTER']='JNTUSDT'
os.environ['ARCHIVE_DATES']='2020-10-06'


class Config:
    key = None
    secret = None
    subaccounts = None
    subaccounts_markets = None
    redis = None
    exposed_redis = None
    ticker_markets = None
    trades_markets = None
    candle_markets = None
    exchanges = None
    markets_filter = None
    archive_dates = None
    markets_csv = None
    workers_count = None
    worker_id = None

    def __init__(self, auth_ftx=True):
        if auth_ftx and ("FTXKEY" not in os.environ or "FTXSECRET" not in os.environ):
            msg = "Error! Could not retrieve FTX key or secret"
            logging.error(msg)
            sys.exit(msg)

        if "COREPACK_FAMILIES" not in os.environ:
            msg = "Error! CorePack families not defined."
            logging.error(msg)
            sys.exit(msg)

        level = logging.getLevelName(os.environ.get("LOG_LEVEL", "INFO"))
        logging.basicConfig(
            level=level,
            format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        logging.info(f"Set logging level to {level}")

        self.key = os.environ.get("FTXKEY")
        self.secret = os.environ.get("FTXSECRET")
        self.subaccounts = os.environ["COREPACK_FAMILIES"].split(",")
        self.subaccounts.append("")
        self.redis = RedisConfig(
            host=os.environ.get("REDIS_NODE_ADDR", "localhost"),
            port=os.environ.get("REDIS_NODE_TCP_PORT", 6379),
            password=os.environ.get("REDIS_PASSWORD", None),
        )
        self.exposed_redis = RedisConfig(
            host=os.environ.get("EXP_REDIS_NODE_ADDR", "localhost"),
            port=os.environ.get("EXP_REDIS_NODE_TCP_PORT", 6379),
            password=os.environ.get("EXP_REDIS_PASSWORD", None),
        )

        ticker_conf = os.environ.get("TICKER_MARKETS", "")
        self.ticker_markets = ticker_conf.split(",") if ticker_conf else []

        trades_conf = os.environ.get("TRADES_MARKETS", "")
        self.trades_markets = trades_conf.split(",") if trades_conf else []

        candle_conf = os.environ.get("CANDLE_MARKETS", "")
        self.candle_markets = candle_conf.split(",") if candle_conf else []

        if any(self.subaccounts):
            logging.info(f"Subscribed to CorePack: {self.subaccounts}")
        if self.ticker_markets:
            logging.info(f"Subscribed to tickers: {self.ticker_markets}")
        if self.candle_markets:
            logging.info(f"Subscribed to candles: {self.candle_markets}")

        self.subaccounts_markets = {}
        for subaccount in self.subaccounts:
            if subaccount:
                books = os.environ.get(subaccount.upper().replace(".", "_"))
                if books:
                    self.subaccounts_markets[subaccount] = books.split(",")

        self.exchanges = os.environ.get("EXCHANGES", "").split(",")
        self.spot_exchanges = os.environ.get("SPOT_EXCHANGES", "").split(",")
        self.markets_filter = os.environ.get("MARKETS_FILTER", "").split(",")
        self.archive_dates = os.environ.get("ARCHIVE_DATES", "").split(",")
        self.markets_csv = os.environ.get("MARKETS_CSV", None)
        self.workers_count = int(os.environ.get("WORKERS_COUNT", 1))
        self.worker_id = int(os.environ.get("WORKER_ID", 0))


async def connect_redis(redis_config, name):
    conn_string = f"redis://{redis_config.host}:{redis_config.port}"
    try:
        redis = await aioredis.create_redis_pool(
            conn_string, password=redis_config.password
        )
    except:
        msg = f"Error connecting to {name} redis: "
        msg += f"{redis_config.host}:{redis_config.port}. "
        msg += f"Redis connection string: {conn_string}"
        logging.error(msg)
        raise
    else:
        return redis
