from paf.tardis_client import bookbuilder
from process_orderflow import process_orderflow
from multiprocess import Pool

books = ["BTC-PERP", "ETH-PERP", "LTC-PERP", "BTC-0626", "BTMX-0327"]
dates = [
    ("2019-11-01T00:00:00", "2019-11-01T23:59:59"),
    ("2019-12-01T00:00:00", "2019-12-01T23:59:00"),
    ("2020-01-01T00:00:00", "2020-01-01T23:59:59"),
    ("2020-02-01T00:00:00", "2020-02-01T23:59:59"),
]
windows = [1, 2, 5, 10]

pool = Pool(2)

args = [(book, date) for book in books for date in dates]
res = pool.starmap(bookbuilder, args)

# args = [(book, windows) for book in orderbooks]
# res = pool.starmap(process_orderflow, args)
pool.close()
