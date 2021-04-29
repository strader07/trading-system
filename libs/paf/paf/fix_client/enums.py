from enum import IntEnum


class State(IntEnum):
    created = 1
    pending = 2
    opened = 3
    partial_fill = 4
    filled = 5
    cancelled = 6
    closed = 7
    unknown = 8
