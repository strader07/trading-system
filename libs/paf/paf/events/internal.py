from dataclasses import dataclass
from typing import List
from paf.events.enums import MDEntryType, Side


@dataclass
class MDEntry:
    # MDUpdateAction: MDUpdateAction
    MDEntryType: MDEntryType
    MDEntryPx: float
    MDEntrySize: float
    MDEntryDate: int
    Aggressor: Side
    # OrdStatus: OrdStatus  # TODO: enum

    def __init__(
        self,
        # MDUpdateAction_,
        MDEntryType_,
        price,
        size,
        Aggressor_,
        MDEntryDate_,
        # OrdStatus,
    ):
        # self.MDUpdateAction = MDUpdateAction(MDUpdateAction_)
        self.MDEntryType = MDEntryType(MDEntryType_)
        self.MDEntryPx = price
        self.MDEntrySize = size
        self.Aggressor = Aggressor_
        self.MDEntryDate = MDEntryDate_
        # self.OrdStatus = OrdStatus


@dataclass
class MarketSnapshot:
    Symbol: str
    SeqNum: int
    TradeVolume24: float
    OpenInterest: float
    NoMDEntries: int
    MDEntries: List[MDEntry]


@dataclass
class MarketRefresh:
    Symbol: str
    SeqNum: int
    TradeVolume24: float
    OpenInterest: float
    NoMDEntries: int
    MDEntries: List[MDEntry]
    MDEntryDate: int


@dataclass
class MatchesWindow:
    max_price: float
    min_price: float
    open_price: float
    close_price: float
    volume: float
    data_points: int


@dataclass
class MarketSummary:
    last_price: float
    high_price: float
    low_price: float
    pct_change: float
    abs_change: float
