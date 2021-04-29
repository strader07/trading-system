import backtrader as bt
import pandas as pd

# Run redis subscribe in a thread/process? async?
# When we get data, set it up in the feed for load to find


class RedisFeed:
    def __init__(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def haslivedata(self):
        return True

    def islive(self):
        return True

    def _load(self):
        # if nodata:
        #     return False

        # Get the rest of the unpacked data
        # o, h, l, c, v, oi = bdata[self.dtsize :]
        self.lines.open[0] = 1
        self.lines.high[0] = 2
        self.lines.low[0] = 3
        self.lines.close[0] = 4
        self.lines.volume[0] = 5
        self.lines.openinterest[0] = 6

        return True
