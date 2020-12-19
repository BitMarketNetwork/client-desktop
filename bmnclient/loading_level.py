import enum

class LoadingLevel(enum.IntEnum):
    NONE = enum.auto()
    ADDRESSES = enum.auto()
    TRANSACTIONS = enum.auto()
    INPUTS = enum.auto()