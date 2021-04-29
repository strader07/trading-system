# ---------------------------------- #
# ----------- DATAFEEDS ------------ #
# ---------------------------------- #

import pandas as pd
import backtrader as bt
from datetime import datetime


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
