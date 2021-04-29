# ------------------------------------------------------------------------------------------------ #
# ------------------------------------ BACKTRADER SKELETON --------------------------------------- #
# --------------------------------- STRATEGIES AND BACKTESTING ----------------------------------- #
# ------------------------------------------ v 2.1 ----------------------------------------------- #
#  ██████╗ ████████╗ ██████╗    ██████╗  █████╗  ██████╗██╗  ██╗████████╗███████╗███████╗████████╗ #
#  ██╔══██╗╚══██╔══╝██╔════╝    ██╔══██╗██╔══██╗██╔════╝██║ ██╔╝╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝ #
#  ██████╔╝   ██║   ██║         ██████╔╝███████║██║     █████╔╝    ██║   █████╗  ███████╗   ██║    #
#  ██╔══██╗   ██║   ██║         ██╔══██╗██╔══██║██║     ██╔═██╗    ██║   ██╔══╝  ╚════██║   ██║    #
#  ██████╔╝   ██║   ╚██████╗    ██████╔╝██║  ██║╚██████╗██║  ██╗   ██║   ███████╗███████║   ██║    #
#  ╚═════╝    ╚═╝    ╚═════╝    ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚══════╝   ╚═╝    #
# ------------------------------------------------------------------------------------------------ #
# ------------------------------------------------------------------------------------------------ #

# ---------------------------------- #
# ------------ IMPORTS ------------- #
# ---------------------------------- #

import backtrader as bt
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
import time

# ---------------------------------- #
# ----------- DATAFEEDS ------------ #
# ---------------------------------- #


def resampleData(bitdf, nx, tf):
    # bitdf = btcDat
    # tf = '3min'
    # nx = -10**5
    bitdata = bitdf[nx:].reset_index(drop=True).copy(deep=True)
    bitdata["time"] = bitdata.time / 1000
    bitdata["time"] = bitdata.time.apply(lambda x: datetime.utcfromtimestamp(x))
    bitdata.columns = ["timestamp", "open", "close", "high", "low", "volume"]
    bitdata["timestamp"] = pd.DatetimeIndex(bitdata["timestamp"])
    bitdata.index = bitdata.timestamp
    bitdata = bitdata.resample("1min").fillna("pad")
    bitdataHigh = bitdata.high.resample(tf).max()
    bitdataLow = bitdata.low.resample(tf).min()
    bitdataOpen = bitdata.open.resample(tf).first()
    bitdataClose = bitdata.close.resample(tf).last()
    bitdataVolume = bitdata.volume.resample(tf).sum()
    bitdataTimestamp = bitdata.timestamp.resample(tf).first()
    bitdat = pd.concat(
        [
            bitdataTimestamp,
            bitdataOpen,
            bitdataHigh,
            bitdataLow,
            bitdataClose,
            bitdataVolume,
        ],
        axis=1,
    )
    bitdat = bitdat.reset_index(drop=True)
    return bitdat


data = bt.feeds.GenericCSVData(
    dataname="testdata/btcx.csv",
    # fromdate='2019-02-01',
    # todate='2019-09-05',
    nullvalue=0.0,
    dtformat=("%Y-%m-%d %H:%M:%S"),
    datetime=6,
    high=3,
    low=4,
    open=1,
    close=2,
    volume=5,
    openinterest=-1,
)

# raw data file, 1 minute frequency
datx = pd.read_csv("testdata/btcusd.csv")

# get 1 hour btc Data
btc1hour = resampleData(datx, -5 * 10 ** 5, "1h")
btc1hour.index = pd.DatetimeIndex(btc1hour["timestamp"])
data1hour = bt.feeds.PandasData(
    dataname=btc1hour[1:], timeframe=bt.TimeFrame.Minutes, compression=60
)

# get 15min btc data
btc15min = resampleData(datx, -5 * 10 ** 5, "15min")
btc15min.index = pd.DatetimeIndex(btc15min["timestamp"])
data15min = bt.feeds.PandasData(
    dataname=btc15min[1:], timeframe=bt.TimeFrame.Minutes, compression=15
)

# get 5min btc data
btc5min = resampleData(datx, -5 * 10 ** 5, "5min")
btc5min.index = pd.DatetimeIndex(btc5min["timestamp"])
data5min = bt.feeds.PandasData(
    dataname=btc5min[1:], timeframe=bt.TimeFrame.Minutes, compression=5
)


# ---------------------------------- #
# ------- DEFINE STRATEIGES -------- #
# ---------------------------------- #


# enter psar, exit ema crossover (
# entry vs. exit
# 5min vs. 2min
# 15min vs. 5min <-- use this one first
# 1hr vs. 15min
class psarEma(bt.Strategy):
    params = dict(emaPeriod=21, psarRate=0.02)

    def __init__(self):
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


import backtrader as bt


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


# class builds a custom trade log
class LogTrades(bt.Analyzer):
    def __init__(self):
        self.logdata = []
        # data columns
        self.logcolumns = [
            "opentime",
            "type",
            "onopen",
            "openquant",
            "openprice",
            "opencomm",
            "closetime",
            "onclose",
            "closequant",
            "closeprice",
            "closecomm",
            "profitloss",
            "pnlcomm",
            "finalcash",
            "finalvalue",
            "totalpnl",
            "totalpnlcomm",
            "drawdown",
            "maxdrawdown",
        ]

        self.type = "long"
        self.onopen = "buy"
        self.onclose = "sell"
        self.opencomm = 0
        self.openprice = 0
        self.openvalue = 0
        self.profitloss = 0
        self.pnlcomm = 0
        self.closeprice = 0
        self.cash = 0
        self.value = 0
        self.ddown = 0
        self.maxdown = 0
        self.ordersize = 0

    def notify_cashvalue(self, cash, value):
        self.cash = cash
        self.value = value

    def notify_trade(self, trade):
        self.ordersize = trade.history[0].event.size
        if self.ordersize < 0:
            self.type = "short"
            self.type, self.onopen, self.onclose = "short", "sell", "buy"
        else:
            self.type, self.onopen, self.onclose = "long", "buy", "sell"
        self.openprice = trade.history[0].event.price
        self.opencomm = trade.history[0].event.commission
        # self.open_value = trade.history[0].event.value
        self.pnlcomm = self.pnlcomm + trade.pnlcomm
        self.profitloss = self.profitloss + trade.pnl
        if trade.isclosed:
            self.closeprice = trade.history[1].event.price
            self.logdata.append(
                [
                    trade.dtopen,
                    self.type,
                    self.onopen,
                    self.ordersize,
                    self.openprice,
                    self.opencomm,
                    trade.dtclose,
                    self.onclose,
                    trade.size - self.ordersize,
                    self.closeprice,
                    trade.commission,
                    trade.pnl,
                    trade.pnlcomm,
                    self.cash,
                    self.value,
                    self.profitloss,
                    self.pnlcomm,
                    self.ddown,
                    self.maxdown,
                ]
            )

    def stop(self):
        (
            pd.DataFrame(self.logdata, columns=self.logcolumns).to_csv(
                f"tradeLog_{stratlabel}_{str(time.time())[:-6]}.csv"
            )
        )


# ---------------------------------- #
# ---------- RUN BACKTEST ---------- #
# ---------------------------------- #


# add below if resampling is required
"""
cereb.resampledata(datafeed,
                   timeframe=bt.TimeFrame.Minutes,
                   compression=15)
"""

datafeeds = [data5min]  # data1hour, data15min, ]
datalabels = ["data5min"]  # 'data1hour', 'data15min', ]

strategies = [psarX]  # psarX, psarEma, mesaX, superTrendX,
# candleTrade, candleLong, candleShort]

stratlabels = [
    # "psarX",
    "psarEma",
    # "mesaX",
    # "superTrendX",
    # "candleTrade",
    # "candleLong",
    # "candleShort",
]
tradeResults = []

# determine which strategy and datafeeds to use
stratlabel = "psarEma"
datalabel = "1hour_15min"

# set optimization to true / false


def runstrat(optimize):
    # # build engine
    cereb = bt.Cerebro(tradehistory=True)
    # convert to heiken candle data
    data1hour.addfilter(bt.filters.HeikinAshi)
    data1hour.addfilter(bt.filters.HeikinAshi)
    data1hour.addfilter(bt.filters.HeikinAshi)

    data15min.addfilter(bt.filters.HeikinAshi)
    data15min.addfilter(bt.filters.HeikinAshi)
    data15min.addfilter(bt.filters.HeikinAshi)

    # xdata.addfilter(bt.filters.HeikinAshi(xdata))
    # xdata.addfilter(bt.filters.HeikinAshi(xdata))
    # add datafeed
    cereb.adddata(data15min, name="smaller")
    cereb.adddata(data1hour, name="larger")
    # include drawdown in results
    cereb.addobserver(bt.observers.DrawDown)
    # cereb.addobserver(bt.observers.BuySell)
    # uncomment if changing strategy
    # declare strategy to test
    # optimization paramaters to test
    if optimize:
        cereb.optstrategy(psarEma, emaPeriod=range(19, 22, 1))
    else:
        cereb.addstrategy(psarEma)
    cereb.addanalyzer(LogTrades)
    # set commission
    # https://www.backtrader.com/docu/commission-schemes/commission-schemes/
    # # samples
    # # cerebro.broker.setcommission(commission=0.005)  # 0.5% of the operation value

    # # cerebro.broker.setcommission(commission=0.00075)  # 0.075% of the operation value
    cereb.broker.setcommission(commission=0.00075, margin=None)

    # starting value
    startvalue = 10000.0
    cereb.broker.set_cash(startvalue)
    # cereb.addwriter(bt.WriterFile, csv=True, out='{}_{}.csv'.format(stratlabel, datalabel))

    # # run backtest
    cereb.run(maxcpus=1)
    return cereb


# run strategy
cereb = runstrat(optimize=False)

# this will produce some analysis of the last result
# if optimize == False
# plot parameters
cereb.plot(style="candlestick", start=dt.date(2019, 12, 5))

# export png
fig = plt.gcf()
fig.set_size_inches(20, 10)
fig.set_tight_layout({"pad": 2})
plotlabel = "{}_{}".format(stratlabel, datalabel)
fig.suptitle(plotlabel, x=0.5, y=0.99)
plt.savefig("tradePlots/{}.png".format(plotlabel))
plt.close()

# # backtest results
startvalue = 10000.0
totalcash = round(cereb.broker.get_cash(), 2)
print("Total Cash:", totalcash)
totalvalue = round(cereb.broker.get_value(), 2)
print("Total Value:", totalvalue)
profit = round(cereb.broker.get_value() - startvalue, 2)
print("Total Profit:", profit)
profitpercent = round(100 * profit / startvalue, 6)
print("Total Profit: {}{}".format(profitpercent, "% change"))
ntrades = len(cereb.broker.orders)
# commissions paid
comms = []
for order in cereb.broker.orders:
    comms.append(order.executed.comm)
# gross profit
totalcomms = np.sum(comms)
grossprofit = profit + totalcomms
# store trade results
tradeResults.append(
    [
        stratlabel,
        datalabel,
        totalcash,
        totalvalue,
        grossprofit,
        totalcomms,
        profit,
        profitpercent,
        ntrades,
    ]
)

import time

tradedf = pd.DataFrame(tradeResults)
tradedf.columns = [
    "strategy",
    "datafeed",
    "total_cash",
    "total_value",
    "gross_profit",
    "total_commissions",
    "net_profit",
    "net_profit_percent",
    "number_trades",
]
tradedf = tradedf.sort_values("net_profit_percent", ascending=False)
xtime = str(time.time())[0:10][-7:]
tradedf.to_csv("backtest_results_{}.csv".format(xtime))
