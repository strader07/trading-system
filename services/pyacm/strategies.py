# ---------------------------------- #
# ------- DEFINE STRATEIGES -------- #
# ---------------------------------- #

from collections import deque
import backtrader as bt
import requests


# enter psar, exit ema crossover (
# entry vs. exit
# 5min vs. 2min
# 15min vs. 5min <-- use this one first
# 1hr vs. 15min
class psarEma:
    params = dict(emaPeriod=21, psarRate=0.02)

    def __init__(self):
        emaPeriod = self.params["emaPeriod"]

        self.ema1data = deque([], emaPeriod)  # 5m
        self.ema2data = deque([], emaPeriod)  # 15m

        r = requests.get(
            "https://www.bitmex.com/api/v1/quote/bucketed?symbol=XBT&count=5&reverse=true&binSize=5m"
        )
        resp = r.json()
        print(resp)

        for candle in reversed(resp):
            self.ema1data.appendleft(candle["close"])

        rr = list(reversed(resp))
        for i in range(0, len(rr), 3):
            self.ema2data.appendleft(rr[i]["close"])

        # TODO: subscribe to redis for live updates, update queue
        # TODO: Send out trade
        # TODO: PSAR

        self.ema1 = bt.ind.EMA(self.data, period=self.p.emaPeriod)
        self.psar = bt.talib.SAR(
            self.data1.high, self.data1.low, acceleration=self.p.psarRate
        )
        self.crossover = bt.ind.CrossOver(self.ema1, self.data.close)
        self.cross2 = bt.ind.CrossOver(self.data1.close, self.psar)

    def next(self):
        if self.cross2[-1] == 1:
            if not self.position:
                self.buy()
        if self.cross2[-1] == -1:
            if not self.position:
                self.sell()

        if self.position:
            if self.position.size < 0:  # short position
                if self.crossover[-1] == -1:
                    self.close()
            if self.position.size > 0:  # long position
                if self.crossover[-1] == 1:
                    self.close()


# psar entry, ema crossover exit
# ignore this - unused
class psarX(bt.Strategy):
    params = dict(psarRate=0.02)

    def __init__(self):
        self.psar = bt.talib.SAR(
            self.data.high, self.data.low, acceleration=self.p.psarRate
        )
        self.cross = bt.ind.CrossOver(self.data.close, self.psar)

    def next(self):
        if not self.position:
            if self.cross == 1:
                self.buy()
            if self.cross == -1:
                self.sell()
        elif self.position:
            if self.cross == -1:
                self.close()
                self.sell()
            if self.cross == 1:
                self.close()
                self.buy()


# adaptive moving average, mama and fama crossover
# ignore that
class mesaX(bt.Strategy):
    params = dict(fastx=0.5, slowx=0.05)

    def __init__(self):
        self.mesa = bt.talib.MAMA((self.data.high + self.data.low) / 2)
        self.crossover = bt.ind.CrossOver(self.mesa.mama, self.mesa.fama)

    def next(self):
        if not self.position:
            if self.crossover == 1:
                self.buy()
            if self.crossover == -1:
                self.sell()
        elif self.position:
            if self.crossover == 1:
                self.close()
                self.buy()
            if self.crossover == -1:
                self.close()
                self.sell()


# https://github.com/mementum/backtrader/pull/374/files
# Supertrend indicator function taken from this link
class SuperTrendBand(bt.Indicator):
    """
    Helper inidcator for Supertrend indicator
    """

    params = (("period", 7), ("multiplier", 3))
    lines = ("basic_ub", "basic_lb", "final_ub", "final_lb")

    def __init__(self):
        self.atr = bt.indicators.AverageTrueRange(period=self.p.period)
        self.l.basic_ub = ((self.data.high + self.data.low) / 2) + (
            self.atr * self.p.multiplier
        )
        self.l.basic_lb = ((self.data.high + self.data.low) / 2) - (
            self.atr * self.p.multiplier
        )

    def next(self):
        if len(self) - 1 == self.p.period:
            self.l.final_ub[0] = self.l.basic_ub[0]
            self.l.final_lb[0] = self.l.basic_lb[0]
        else:
            # =IF(OR(basic_ub<final_ub*,close*>final_ub*),basic_ub,final_ub*)
            if (
                self.l.basic_ub[0] < self.l.final_ub[-1]
                or self.data.close[-1] > self.l.final_ub[-1]
            ):
                self.l.final_ub[0] = self.l.basic_ub[0]
            else:
                self.l.final_ub[0] = self.l.final_ub[-1]

            # =IF(OR(baisc_lb > final_lb *, close * < final_lb *), basic_lb *, final_lb *)
            if (
                self.l.basic_lb[0] > self.l.final_lb[-1]
                or self.data.close[-1] < self.l.final_lb[-1]
            ):
                self.l.final_lb[0] = self.l.basic_lb[0]
            else:
                self.l.final_lb[0] = self.l.final_lb[-1]


class SuperTrend(bt.Indicator):
    """
    Super Trend indicator
    """

    params = (("period", 1), ("multiplier", 1))
    lines = ("super_trend",)
    plotinfo = dict(subplot=False)

    def __init__(self):
        self.stb = SuperTrendBand(period=self.p.period, multiplier=self.p.multiplier)

    def next(self):
        if len(self) - 1 == self.p.period:
            self.l.super_trend[0] = self.stb.final_ub[0]
            return

        if self.l.super_trend[-1] == self.stb.final_ub[-1]:
            if self.data.close[0] <= self.stb.final_ub[0]:
                self.l.super_trend[0] = self.stb.final_ub[0]
            else:
                self.l.super_trend[0] = self.stb.final_lb[0]

        if self.l.super_trend[-1] == self.stb.final_lb[-1]:
            if self.data.close[0] >= self.stb.final_lb[0]:
                self.l.super_trend[0] = self.stb.final_lb[0]
            else:
                self.l.super_trend[0] = self.stb.final_ub[0]


#
class candleTrade(bt.Strategy):
    def next(self):
        if self.data.close[-1] > self.data.open[-1]:
            if self.data.close[0] < self.data.open[0]:
                if self.position:
                    self.close()
                    self.sell()
                else:
                    self.sell()
        else:
            if self.data.close[0] > self.data.open[0]:
                if self.position:
                    self.close()
                    self.buy()
                else:
                    self.buy()


class candleShort(bt.Strategy):
    def next(self):
        if self.data.close[-1] > self.data.open[-1]:
            if self.data.close[0] < self.data.open[0]:
                if not self.position:
                    self.sell()
        else:
            if self.data.close[0] > self.data.open[0]:
                if self.position:
                    self.close()


class candleLong(bt.Strategy):
    def next(self):
        if self.data.close[-1] > self.data.open[-1]:
            if self.data.close[0] < self.data.open[0]:
                if self.position:
                    self.close()
        else:
            if self.data.close[0] > self.data.open[0]:
                if not self.position:
                    self.buy()


# convert indicator to strategy
# ignore
class superTrendX(bt.Strategy):
    def __init__(self):
        self.supertrend = SuperTrend(self.data)
        self.crossover = bt.ind.CrossOver(self.supertrend, self.data.close)

    def next(self):

        if self.crossover == -1:
            if self.position:
                self.close()
                self.buy()
            else:
                self.buy()
        if self.crossover == 1:
            if self.position:
                self.close()
                self.sell()
            else:
                self.sell()

        """if not self.position:
            if self.crosshigh == -1:
                self.buy()
            if self.crosslow == 1:
                self.sell()
        elif self.position:
            if self.crosshigh == -1:
                self.close()
                self.buy()
            if self.crosslow == 1:
                self.close()
                self.sell()"""
