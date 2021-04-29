import asyncio
import os
import aiohttp
from datetime import datetime

URL = "ws://localhost:8000/ws-replay?exchange=ftx&from=2020-02-10&to=2020-02-11"


async def replay():
    session = aiohttp.ClientSession()

    async with session.ws_connect(URL) as websocket:
        await websocket.send_str(
            '{"op": "subscribe", "channel": "trades", "market": "BTC-PERP"}'
        )
        await websocket.send_str(
            '{"op": "subscribe", "channel": "orderbook", "market": "BTC-PERP"}'
        )
        count = 0
        print("started", datetime.today(), flush=True)
        async for msg in websocket:
            # print(msg)
            count = count + 1
            if msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                print(f"error: {msg}")
                break
        print("finished", datetime.today(), count, flush=True)


asyncio.run(replay())
