import random


class RandomSignal:
    """
    Random Signal Generator.

    If flat:
    20% long
    20% short
    60% remain flat

    If long:
    10% cancel
    15% flip short

    If short:
    10% cancel
    15% flip long
    """

    def __init__(self):
        self.state = 0

    def process(self, val):
        r = random.random()

        if self.state == 0:
            if r < 0.2:
                self.state = 1
            elif r < 0.4:
                self.state = -1

        elif self.state == 1:
            if r < 0.1:
                self.state = 0
            elif r < 0.15:
                self.state = -1

        elif self.state == -1:
            if r < 0.1:
                self.state = 0
            elif r < 0.15:
                self.state = 1

        return self.state
