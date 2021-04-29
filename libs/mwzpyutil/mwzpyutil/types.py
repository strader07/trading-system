from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


@dataclass
class Ticker:
    market: str
    bid_px: float
    bid_qty: float
    ask_px: float
    ask_qty: float
    last: float
    time: str

    def __str__(self):
        return f"{self.bid_px},{self.bid_qty},{self.ask_px},{self.ask_qty},{self.last},{self.time}"


@dataclass
class Candle:
    open_: float
    close: float
    high: float
    low: float
    volume: float
    startTime: datetime
    time: str

    def score(self):
        return self.time

    def __str__(self):
        return f"{self.open_},{self.close},{self.high},{self.low},{self.volume}"


@dataclass
class Trade:
    market: str
    id: int
    time: datetime
    price: float
    size: float
    side: str
    liquidation: bool


class MarketType(Enum):
    spot = 0
    future = 1
    move = 2
    perpetual = 3
    prediction = 4


@dataclass
class Market:
    exchange: str
    market: str
    instrument: str
    type_: MarketType
    enabled: bool
    maker_fee: float
    taker_fee: float
    tick_size: float
    min_size: float
    price_precision: float
    size_precision: float
    mm_size: float
    expiry: datetime

    # TODO: setup instrument here.
    # move to pymwzutil and make exchange agnostic
    # def __post_init__(self):
    #     pass

    # TODO: support underlying with full y/m/d
    # FTX changes name to: BCH-20190329


@dataclass
class Fill:
    id_: int
    market: str
    order_id: int
    price: float
    size: float
    side: str
    fee: float
    fee_rate: float
    liquidity: str
    time: str  # todo: datetime

    def to_dict(self):
        return {
            "id": self.id_,
            "market": self.market,
            "order_id": self.order_id,
            "price": self.price,
            "size": self.size,
            "side": self.side,
            "fee": self.fee,
            "fee_rate": self.fee_rate,
            "liquidity": self.liquidity,
            "time": self.time,
        }


@dataclass
class RunningFill:
    sum_prod_px_sz: float
    total_size: float

    def add_fill(self, price, size, side):
        sign = 1 if side == "buy" else -1
        price_size = price * size
        self.sum_prod_px_sz += price_size * sign
        self.total_size += size * sign

    def avg_price(self):
        return 0 if self.total_size == 0 else self.sum_prod_px_sz / self.total_size

