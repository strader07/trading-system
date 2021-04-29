from app.utils import RawFile, FileType
import pyarrow.parquet as pq
from mwzpyutil import logger


async def generate_parquet_files(book, settings):
    book_table, trades_table = book.build_lob_table()
    base_name = "{exchange}_{instrument}_{date}_{kind}.parquet"
    book_file = base_name.format(
        exchange=settings.market.exchange,
        instrument=settings.market.instrument,
        date=settings.date,
        kind="lob",
    )
    trades_file = base_name.format(
        exchange=settings.market.exchange,
        instrument=settings.market.instrument,
        date=settings.date,
        kind="trades",
    )

    raw_files = []
    if book_table:
        pq.write_table(book_table, book_file, coerce_timestamps="us")
        raw_files.append(RawFile(book_file, FileType.BOOK,))
    else:
        logger.warn("Book table empty")
    if trades_table:
        pq.write_table(trades_table, trades_file, coerce_timestamps="us")
        raw_files.append(RawFile(trades_file, FileType.TRADES,))
    else:
        logger.warn("Trades empty")
    return raw_files
