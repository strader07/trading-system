from dataclasses import dataclass
from datetime import datetime
from paf.events.enums import Side


@dataclass
class Trade:
    symbol: str
    id_: int
    price: float
    size: float
    side: Side
    liquidation: bool
    date: datetime
    timestamp: str


@dataclass
class Quote:
    symbol: str
    price: float
    size: float
    side: Side
    date: datetime
    timestamp: str
