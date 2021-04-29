import asyncio
import csv
from datetime import timedelta, date, datetime
from app.utils import get_markets, RunSettings


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


class Config:
    key = ""
    secret = ""
    markets_csv = ""


def get_markets_listing():
    markets_listed_at = {}
    with open("ftx_markets_filter.csv") as f:
        reader = csv.reader(f, delimiter=",")
        next(reader)
        for row in reader:
            market = row[0]
            try:
                listed_at = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                listed_at = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
            markets_listed_at[market] = listed_at
    return markets_listed_at


def normalize_mkt(market):
    return market.replace("-2019", "-")


async def get_all_jobs():
    config = Config()
    markets = await get_markets(config)
    markets_listed_at = get_markets_listing()

    with open("markets.csv", mode="w") as markets_file:
        markets_writer = csv.writer(
            markets_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        markets_writer.writerow(["market", "instrument", "type", "enabled", "expiry"])
        for market in markets:
            markets_writer.writerow(
                [
                    market.market,
                    market.instrument,
                    market.type_,
                    market.enabled,
                    market.expiry,
                ]
            )

    jobs = {}

    start = date(2019, 8, 8)
    end = date(2020, 4, 3)
    for dt in daterange(start, end):
        dt_markets = []
        for market in markets:
            if market.expiry and market.expiry.date() < dt:
                continue
            elif (
                market.market in markets_listed_at
                and markets_listed_at[market.market].date() > dt
            ):
                continue
            dt_markets.append(market)
        jobs[dt] = dt_markets

    with open("jobs.csv", mode="w") as jobs_file:
        jobs_writer = csv.writer(
            jobs_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        for dt, markets in jobs.items():
            dt_markets = [m.instrument for m in markets]
            jobs_writer.writerow([f'{dt.strftime("%Y-%m-%d")}', ",".join(dt_markets)])


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_all_jobs())
