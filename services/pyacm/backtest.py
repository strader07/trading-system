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

import backtrader as bt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
import time

from csv_feed import data5min, data15min, data1hour
from strategies import psarEma, psarX
from logtrades import LogTrades


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
datalabel = "15min_5min"

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


# def runlive(optimize):
#     cereb = bt.Cerebro(tradehistory=True)

#     # create live feeds
#     # convert to heiken candle data
#     data1hour.addfilter(bt.filters.HeikinAshi)
#     data1hour.addfilter(bt.filters.HeikinAshi)
#     data1hour.addfilter(bt.filters.HeikinAshi)
#     data15min.addfilter(bt.filters.HeikinAshi)
#     data15min.addfilter(bt.filters.HeikinAshi)
#     data15min.addfilter(bt.filters.HeikinAshi)
#     cereb.adddata(data15min, name="smaller")
#     cereb.adddata(data1hour, name="larger")
#     # include drawdown in results
#     cereb.addobserver(bt.observers.DrawDown)
#     # cereb.addobserver(bt.observers.BuySell)
#     # uncomment if changing strategy
#     # declare strategy to test
#     # optimization paramaters to test
#     if optimize:
#         cereb.optstrategy(psarEma, emaPeriod=range(19, 22, 1))
#     else:
#         cereb.addstrategy(psarEma)
#     cereb.addanalyzer(LogTrades)
#     # set commission
#     # https://www.backtrader.com/docu/commission-schemes/commission-schemes/
#     # # samples
#     # # cerebro.broker.setcommission(commission=0.005)  # 0.5% of the operation value

#     # # cerebro.broker.setcommission(commission=0.00075)  # 0.075% of the operation value
#     cereb.broker.setcommission(commission=0.00075, margin=None)

#     # starting value
#     startvalue = 10.0
#     cereb.broker.set_cash(startvalue)
#     # cereb.addwriter(bt.WriterFile, csv=True, out='{}_{}.csv'.format(stratlabel, datalabel))

#     # run live
#     cereb.run(maxcpus=1)
#     return cereb


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
