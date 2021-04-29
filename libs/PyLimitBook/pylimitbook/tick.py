#!/usr/bin/python


class Tick:
    def __init__(self, data):
        self.timestamp = float(data["timestamp"])
        self.qty = float(data["qty"])
        self.price = convert_price(data["price"], False)
        self.id_num = data["id_num"]

    def __str__(self):
        return f"{self.timestamp} - {self.id_num}: {self.qty} @ {self.price}"


def convert_price(price, use_float):
    """
    Converts price to an integer representing a satoshi.
    1 satoshi = 0.00000001
    Smallest representable size is 0.00000001
    """
    if use_float:
        # Use floats to approximate prices instead of exact representation
        return int(float(price) * float(100000000))
    else:
        # Exact representation
        try:
            idx = price.index(".")
        except ValueError as e:
            return int(price)
        concat = "%s%s" % (price[0:idx], price[idx + 1 :].ljust(8, "0")[0:8])
        return int(concat)
        # from decimal import Decimal
        # return int(Decimal(price) * Decimal(10000))


class Trade(Tick):
    def __init__(self, data):
        super().__init__(data)


class Ask(Tick):
    def __init__(self, data):
        super().__init__(data)
        self.is_bid = False


class Bid(Tick):
    def __init__(self, data):
        super().__init__(data)
        self.is_bid = True
