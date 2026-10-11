from enum import Enum

class LibraryActionType(str, Enum):
    BORROW = "borrow"
    RENT = "rent"
    RETURN = "return"
    BUY = "buy"
    SELL = "sell"
