import backtrader as bt
import matplotlib.pyplot as plt
import pandas as pd
import time

stratlabel = "psarEma"

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
