import aiohttp
import asyncio
import logging
import time
import hmac
import json
import os
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse, urlencode, quote_plus


class State(Enum):
    OPEN = 0
    CLOSED = 1
    RECONNECT = 2


class WSChannel:
    name = None
    market = None
    state = State.CLOSED
    on_message = None
    on_reconnect = None

    def __init__(self, channel_name, cb, market=None, on_reconnect=None):
        self.name = channel_name
        self.on_message = cb
        self.market = market
        self.on_reconnect = on_reconnect

    def should_reconnect(self):
        return self.state is State.RECONNECT and self.on_reconnect

    def __str__(self):
        return f"WSChannel[{self.name} - {self.market} | {self.state}]"

    @staticmethod
    def to_ftx_filters(ws_channels):
        channels_filters = {}  # channel: [symbols]
        for channel in ws_channels:
            if channel.name in channels_filters:
                channels_filters[channel.name].append(channel.market)
            else:
                channels_filters[channel.name] = [channel.market]

        filters = []
        for channel, symbols in channels_filters.items():
            filters.append({"channel": channel, "symbols": symbols})

        return filters


class FtxClient:
    _ENDPOINT = "https://ftx.com/api/"
    _WS_ENDPOINT = "wss://ftx.com/ws/"

    def __init__(self, api_key=None, api_secret=None, subaccount_name=None) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._subaccount_name = subaccount_name
        self._http_replay_options = {}

    def set_historical_mode(self, from_date, to_date):
        # TODO:
        # - Support tardis kubernets in live?
        # - does not work with live. Normalize live/replay and ws/http.
        baseurl = (
            "tardis-machine.development.svc.cluster.local"
            if os.environ.get("KUBERNETES_SERVICE_HOST")
            else "localhost"
        )
        replay_options = {"exchange": "ftx", "from": from_date, "to": to_date}
        options = urlencode(replay_options)
        self._WS_ENDPOINT = f"ws://{baseurl}:8000/ws-replay?{options}"
        self._ENDPOINT = "http://{}:8000/replay?options={}".format(baseurl, "{options}")
        self._http_replay_options = {
            "exchange": "ftx",
            "from": from_date,
            "to": to_date,
            "filters": [],
        }

    def get_http_endpoint(self, replay_options):
        return self._ENDPOINT.format(options=quote_plus(json.dumps(replay_options)))

    async def _get(
        self, path: str, params: Optional[Dict[str, Any]] = None, suppress=False
    ) -> Any:
        return await self._request("GET", path, params=params, suppress=suppress)

    async def _post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return await self._request("POST", path, json=params)

    async def _delete(
        self, path: str, params: Optional[Dict[str, Any]] = None, suppress=False
    ) -> Any:
        return await self._request("DELETE", path, json=params)

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        async with aiohttp.ClientSession() as session:
            path = urljoin(self._ENDPOINT, path)

            uripath = urlparse(path).path
            if "params" in kwargs and kwargs["params"]:
                uripath += "?" + urlencode(kwargs["params"], quote_via=quote_plus)

            ts = int(time.time() * 1000)
            signature_payload = f"{ts}{method.upper()}{uripath}"
            if "json" in kwargs:
                signature_payload += json.dumps(kwargs["json"])
            signature = hmac.new(
                self._api_secret.encode(), signature_payload.encode(), "sha256"
            ).hexdigest()

            headers = {
                "FTX-KEY": self._api_key,
                "FTX-SIGN": signature,
                "FTX-TS": str(ts),
            }

            if self._subaccount_name:
                headers["FTX-SUBACCOUNT"] = self._subaccount_name

            suppress = False
            if "suppress" in kwargs:
                suppress = kwargs["suppress"]
                del kwargs["suppress"]

            async with session.request(
                method.lower(), urljoin(self._ENDPOINT, path), headers=headers, **kwargs
            ) as resp:
                res = await self._process_response(resp, suppress=suppress)
                return res

    async def _process_response(
        self, response: aiohttp.ClientResponse, suppress=False
    ) -> Any:
        try:
            data = await response.json()
        except ValueError:
            logging.error("HTTP error")
            response.raise_for_status()
            raise
        else:
            if not data["success"]:
                if not suppress:
                    logging.error(
                        f"Error {response.url} {self._subaccount_name}: {data['error']} | {data}"
                    )
                return
            return data["result"]

    async def get_markets(self) -> List[dict]:
        return await self._get("markets")

    async def get_futures(self) -> List[dict]:
        return await self._get("futures")

    async def get_expired_futures(self) -> List[dict]:
        return await self._get("expired_futures")

    async def get_orderbook(self, market: str, depth: int = None) -> dict:
        return await self._get(f"markets/{market}/orderbook", {"depth": depth})

    async def get_trades(self, market: str, limit: int) -> dict:
        return await self._get(f"markets/{market}/trades", {"limit": limit})

    async def get_candles(
        self,
        market: str,
        resolution: int,
        limit: int = None,
        start_time: datetime = None,
        end_time: datetime = None,
    ) -> dict:
        params = {}
        if resolution:
            params["resolution"] = resolution
        if limit:
            params["limit"] = limit
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        return await self._get(f"markets/{market}/candles", params)

    async def get_account_info(self, suppress=False) -> dict:
        return await self._get(f"account", suppress=suppress)

    async def get_open_orders(self, market: str = None) -> List[dict]:
        # , {"market": market}
        return await self._get(f"orders")

    async def get_conditional_orders(self, market: str = None) -> List[dict]:
        return await self._get(f"conditional_orders", {"market": market})

    async def place_order(
        self,
        market: str,
        side: str,
        price: float,
        size: float,
        type: str = "limit",
        reduce_only: bool = False,
        ioc: bool = False,
        post_only: bool = False,
        client_id: str = None,
    ) -> dict:
        return await self._post(
            "orders",
            {
                "market": market,
                "side": side,
                "price": price,
                "size": size,
                "type": type,
                "reduceOnly": reduce_only,
                "ioc": ioc,
                "postOnly": post_only,
                "clientId": client_id,
            },
        )

    async def place_conditional_order(
        self,
        market: str,
        side: str,
        size: float,
        type: str = "stop",
        limit_price: float = None,
        reduce_only: bool = False,
        cancel: bool = True,
        trigger_price: float = None,
        trail_value: float = None,
    ) -> dict:
        """
        To send a Stop Market order, set type='stop' and supply a trigger_price
        To send a Stop Limit order, also supply a limit_price
        To send a Take Profit Market order, set type='trailing_stop' and supply a trigger_price
        To send a Trailing Stop order, set type='trailing_stop' and supply a trail_value
        """
        assert type in ("stop", "take_profit", "trailing_stop")
        assert (
            type not in ("stop", "take_profit") or trigger_price is not None
        ), "Need trigger prices for stop losses and take profits"
        assert type not in ("trailing_stop") or (
            trigger_price is None and trail_value is not None
        ), "Trailing stops need a trail value and cannot take a trigger price"

        return await self._post(
            "conditional_orders",
            {
                "market": market,
                "side": side,
                "triggerPrice": trigger_price,
                "size": size,
                "reduceOnly": reduce_only,
                "type": "stop",
                "cancelLimitOnTrigger": cancel,
                "orderPrice": limit_price,
            },
        )

    async def cancel_order(self, order_id: str) -> dict:
        return await self._delete(f"orders/{order_id}")

    async def cancel_orders(
        self,
        market_name: str = None,
        conditional_orders: bool = False,
        limit_orders: bool = False,
    ) -> dict:
        return await self._delete(
            f"orders",
            {
                "market": market_name,
                "conditionalOrdersOnly": conditional_orders,
                "limitOrdersOnly": limit_orders,
            },
        )

    async def get_fills(self) -> List[dict]:
        return await self._get(f"fills")

    async def get_balances(self) -> List[dict]:
        return await self._get("wallet/balances")

    async def get_all_balances(self) -> List[dict]:
        return await self._get("wallet/all_balances")

    async def get_deposit_address(self, ticker: str) -> dict:
        return await self._get(f"wallet/deposit_address/{ticker}")

    async def get_positions(self, show_avg_price: bool = False) -> List[dict]:
        return await self._get("positions", {"showAvgPrice": str(show_avg_price)})

    async def get_position(self, name: str, show_avg_price: bool = False) -> dict:
        pos = await self.get_positions(show_avg_price)
        if not pos:
            return {}
        return next(filter(lambda x: x["future"] == name, pos), None,)

    async def get_market_making_stats(self) -> List[dict]:
        return await self._get(
            "stats/market_making", {"onlyShowPassingSnapshots": "true"}
        )

    async def get_all_market_making_stats(self) -> List[dict]:
        return await self._get(
            "stats/market_making", {"onlyShowPassingSnapshots": "false"}
        )

    async def get_month_market_making_stats(self) -> List[dict]:
        return await self._get(
            "stats/market_making/current", {"onlyShowPassingSnapshots": "true"}
        )

    async def get_all_month_market_making_stats(self) -> List[dict]:
        return await self._get(
            "stats/market_making/current", {"onlyShowPassingSnapshots": "false"}
        )

    async def get_pnl(self) -> dict:
        return await self._get("pnl/historical_changes")

    async def subscribe_http(self, ws_channels):
        channel_to_cb = {ws.name: ws.on_message for ws in ws_channels}

        self._http_replay_options["filters"] = WSChannel.to_ftx_filters(ws_channels)
        timeout = aiohttp.ClientTimeout(total=0)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = self.get_http_endpoint(self._http_replay_options)

            async with session.get(url) as response:
                response.content._high_water = 100_000_000

                async for line in response.content:
                    data = json.loads(line.decode())["message"]
                    if isinstance(data, str):
                        err = f"Error: {data}"
                        logging.error(err)
                        raise RuntimeError(err)
                    if data["type"] == "subscribed":
                        continue
                    if data["type"] == "error":
                        logging.error(f"FTX feed error: {data}")
                        continue
                    elif "data" not in data:
                        logging.error(f"Error, data missing: {data}")
                        continue

                    try:
                        channel = data["channel"]
                        on_message = channel_to_cb[channel]
                    except:
                        logging.error(
                            f"Channel {channel} does not have a registered callback. {channel_to_cb}"
                        )
                        continue
                    try:
                        await on_message(data)
                    except Exception as e:
                        logging.error(
                            f"Error calling callback for {channel}: {channel_to_cb} - {on_message}"
                        )
                        raise e

    async def subscribe_ws(self, ws_channels):
        channel_to_cb = {ws.name: ws.on_message for ws in ws_channels}

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self._WS_ENDPOINT, heartbeat=12) as ws:

                # Login
                if self._api_key and self._api_secret:
                    ts = int(time.time() * 1000)
                    signature_payload = f"{ts}websocket_login".encode()
                    signature = hmac.new(
                        self._api_secret.encode(), signature_payload, "sha256"
                    ).hexdigest()
                    login = {
                        "op": "login",
                        "args": {"key": self._api_key, "sign": signature, "time": ts,},
                    }
                    if self._subaccount_name:
                        login["args"]["subaccount"] = self._subaccount_name

                    try:
                        # TODO: log login
                        await ws.send_str(json.dumps(login))
                    except TypeError as e:
                        logging.error(f"Error parsing: {login}")
                        raise e

                # Send subscriptions
                for ws_channel in ws_channels:
                    sub = {"op": "subscribe", "channel": ws_channel.name}
                    if ws_channel.market:
                        sub["market"] = ws_channel.market
                    try:
                        await ws.send_str(json.dumps(sub))
                    except TypeError as e:
                        logging.error(f"Error parsing: {sub}")
                        raise e
                    if ws_channel.should_reconnect():
                        await ws_channel.on_reconnect()
                    ws_channel.state = State.OPEN

                closed = False

                while True:
                    msg = await ws.receive()

                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        if data["type"] == "subscribed":
                            logging.info("WS subscribed")
                            continue
                        if data["type"] == "error":
                            logging.error(f"FTX feed error: {data}")
                            continue
                        elif "data" not in data:
                            logging.error(f"Error, data missing: {data}")
                            continue

                        try:
                            channel = data["channel"]
                            on_message = channel_to_cb[channel]
                        except:
                            logging.error(
                                f"Channel {channel} does not have a registered callback. {channel_to_cb}"
                            )
                            continue
                        try:
                            await on_message(data)
                        except Exception as e:
                            logging.error(
                                f"Error calling callback for {channel}: {channel_to_cb} - {on_message}"
                            )
                            raise e

                    elif msg.type in (
                        aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.CLOSE,
                    ):
                        if msg.data != 1000:
                            closed = True
                            for ws_channel in ws_channels:
                                ws_channel.state = State.RECONNECT
                                logging.error(
                                    f"WS closed. Msg: {msg}. Channel: {ws_channel}. Setting state to reconnect."
                                )
                            await ws.close()
                            break

                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        errmsg = f"WS ERROR: {msg}"
                        logging.error(errmsg)
                        for ws_channel in ws_channels:
                            ws_channel.state = State.CLOSED
                        raise RuntimeError(errmsg)

                    else:
                        logging.error(f"Unknown WS message type: {msg}")

                if closed:
                    logging.info("WS closed, reconnecting.")
                    await self.subscribe_ws(ws_channels)
