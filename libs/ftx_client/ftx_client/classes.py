from dataclasses import dataclass
from datetime import datetime, timezone


class MMStats:
    market = None
    subaccounts = None

    class Stats:
        bbo_pct = 0
        deep_pct = 0
        bbo_snaps = 0
        deep_snaps = 0

    def __init__(self, market):
        self.market = market
        self.subaccounts = set()
        self.today_stats = self.Stats()
        self.month_stats = self.Stats()

    def add_today_stat(self, bbo_pct, deep_pct, subaccount):
        if subaccount:
            self.subaccounts.add(subaccount)
        self.today_stats.bbo_pct += bbo_pct
        self.today_stats.deep_pct += deep_pct

        possible_snaps = self.today_possible_snaps()
        self.today_stats.bbo_snaps += possible_snaps * bbo_pct
        self.today_stats.deep_snaps += possible_snaps * deep_pct

    def add_month_stat(self, bbo_pct, deep_pct, subaccount):
        if subaccount:
            self.subaccounts.add(subaccount)
        self.month_stats.bbo_pct += bbo_pct
        self.month_stats.deep_pct += deep_pct

        possible_snaps = self.month_possible_snaps()
        self.month_stats.bbo_snaps += possible_snaps * bbo_pct
        self.month_stats.deep_snaps += possible_snaps * deep_pct

    @staticmethod
    def today_possible_snaps():
        date = datetime.now(timezone.utc)
        possible_snaps = date.hour * 2
        if date.minute > 30:
            possible_snaps += 1
        return possible_snaps

    @staticmethod
    def month_possible_snaps():
        date = datetime.now(timezone.utc)
        possible_snaps = (date.day - 1) * 48
        possible_snaps += MMStats.today_possible_snaps()
        return possible_snaps
