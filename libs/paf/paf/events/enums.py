from enum import Enum, IntEnum


class MDUpdateAction(IntEnum):
    UNINITIALIZED = -1
    NEW = 0
    CHANGE = 1
    DELETE = 2


class MDEntryType(IntEnum):
    UNINITIALIZED = -1
    BID = 0
    OFFER = 1
    TRADE = 2
    INDEX_VALUE = 3


class Side(IntEnum):
    UNINITIALIZED = -1
    BID = 1
    ASK = 2

    @staticmethod
    def from_signal(signal):
        if signal == 1:
            return Side.BID
        elif signal == -1:
            return Side.ASK
        elif signal == 0:
            return Side.UNINITIALIZED

    @staticmethod
    def from_string(str):
        if str in ("buy", "bid"):
            return Side.BID
        elif str in ("sell", "ask"):
            return Side.ASK
        else:
            raise ValueError(f"Invalid side str: {str}")

    @staticmethod
    def to_string(side):
        if side == Side.BID:
            return "buy"
        elif side == Side.ASK:
            return "sell"
        else:
            raise ValueError(f"Invalid to_string side : {side}")


class OrdStatus(Enum):
    UNINITIALIZED = -1
    NEW = 0
    PARTIALLY_FILLED = 1
    FILLED = 2
    DONE = 3
    CANCELED = 4
    REPLACED = 5
    PENDING_CANCEL = 6
    STOPPED = 7
    REJECTED = 8
    SUSPENDED = 9
    PENDING_NEW = "A"
