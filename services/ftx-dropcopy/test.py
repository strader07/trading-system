import os
import asyncio
from mwzpyutil import Config, connect_redis

os.environ["FTXSECRET"] = ""
os.environ["FTXKEY"] = ""
os.environ["COREPACK_FAMILIES"] = ""
os.environ["EXP_REDIS_NODE_ADDR"] = "redis-exposed.ftx.dev.muwazana.com"
os.environ["EXP_REDIS_PASSWORD"] = "2sx8ieUNDbfTRwanVJMPnVCBerMV2fjhC8hBBBho"
config = Config()


async def main():
    exp_redis = await connect_redis(config.exposed_redis, "exposed")
    ret = await exp_redis.hmget("ftx:ATOMM20", "clOrdID")
    clord = ret[0]
    print(clord)
    print(ret)
    print(type(ret))


asyncio.run(main())
