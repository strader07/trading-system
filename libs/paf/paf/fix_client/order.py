from paf.fix_client.enums import State


class Order:
    global_clOrdID = 1

    def __init__(self, price, size, side, state=State.created):
        self.clOrdID = Order.global_clOrdID
        Order.global_clOrdID += 1
        self.price = price  # tround(price, 0.5)  # replace 0.5 with tick_size
        self.size = size
        self.side = side
        self.state = state

    @staticmethod
    def get_next_id():
        clOrdID = Order.global_clOrdID
        Order.global_clOrdID += 1
        return clOrdID
