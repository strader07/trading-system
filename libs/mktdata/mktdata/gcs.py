import os
import sys
from datetime import date
from enum import Enum
from google.cloud import storage
from google.api_core import exceptions
import pandas as pd


class MktDataFiles:
    def __init__(self, book=None, trades=None):
        self.book = book
        self.trades = trades
        self.refdata = None


class MktDataDF:
    def __init__(self, book=None, trades=None):
        self.book = book
        self.trades = trades
        self.refdata = None


class Filter(Enum):
    BOOK = 0
    TRADES = 1
    REFDATA = 2


def _get_gcs_path(kind: str, exchange: str, market: str, date_: date):
    dtstr = date_.strftime("%Y-%m-%d")
    fname = f"{market}_{dtstr}_{kind}.parquet"
    return f"{kind}/{exchange}/{market}/{date_.year}/{date_.month}/{date_.day}/{fname}"


def _parquet_as_df(file):
    try:
        df = pd.read_parquet(file)
    except OSError as e:
        err = getattr(e, "message", str(e))
        e.__traceback__ = None
        raise OSError(f"Error in parquet file {file}: {err}")
    df.set_index("time", inplace=True, drop=True)
    return df


def _list_blobs_with_prefix(bucket_name, prefix):
    storage_client = storage.Client()

    blobs = storage_client.list_blobs(bucket_name, prefix=prefix, delimiter=None)

    output = []
    for blob in blobs:
        if "parquet" in blob.name:
            output.append(f"gs://{bucket_name}/{blob.name}")

    return output


def download_file(storage_client, exchange, kind, market, date_, dst=None):
    srcpath = _get_gcs_path(kind, exchange, market, date_)
    dstpath = (
        os.path.basename(srcpath) if not dst else f"{dst}/{os.path.basename(srcpath)}"
    )
    if os.path.isfile(dstpath):
        return dstpath
    else:
        bucket = storage_client.bucket("raw_mktdata")
        blob = bucket.blob(srcpath)
        try:
            blob.download_to_filename(dstpath)
        except Exception as e:
            if os.path.isfile(dstpath):
                os.remove(dstpath)
            e.__traceback__ = None
            raise exceptions.NotFound(f"MktData file not found: {dstpath}")
        return dstpath


def get_raw_mktdata(exchange: str, market: str, date_: date, dst=None, filters=None):
    if not filters:
        filters = [filt for filt in Filter]
    elif not isinstance(filters, list):
        raise ValueError("Filters must be a list.")

    if dst:
        try:
            os.mkdir(dst)
        except FileExistsError:
            pass

    client = storage.Client()
    book_file = trades_file = None
    if Filter.BOOK in filters:
        book_file = download_file(client, exchange, "book", market, date_, dst)
    if Filter.TRADES in filters:
        trades_file = download_file(client, exchange, "trades", market, date_, dst)
    return MktDataFiles(book_file, trades_file)


def get_df_raw_mktdata(exchange: str, market: str, date_: date, filters=None):
    if not filters:
        filters = [filt for filt in Filter]
    elif not isinstance(filters, list):
        raise ValueError("Filters must be a list.")

    book_df = trades_df = None

    if Filter.BOOK in filters:
        book_file = _get_gcs_path("book", exchange, market, date_)
        book_df = _parquet_as_df(f"gs://raw_mktdata/{book_file}")
    if Filter.TRADES in filters:
        trades_file = _get_gcs_path("trades", exchange, market, date_)
        trades_df = _parquet_as_df(f"gs://raw_mktdata/{trades_file}")

    return MktDataFiles(book_df, trades_df)


def get_feature_df(bucket, prefix):
    paths = _list_blobs_with_prefix(bucket, prefix)
    return pd.concat(pd.read_parquet(parquet_file) for parquet_file in paths)


# TODO
# def get_intermediate_mktdata(exchange, market, day):
#     return MktData()


# def get_feature_mktdata(exchange, market, day):
#     return MktData()


def list_files(bucket_name, folder):
    storage_client = storage.Client()

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket_name, prefix=folder, delimiter="/")

    files = [str(blob.name) for blob in blobs]
    subdirs = [str(prefix) for prefix in blobs.prefixes]
    return files, subdirs


## General helpers


def list_blobs(bucket_name):
    """Lists all the blobs in the bucket."""
    # bucket_name = "your-bucket-name"

    storage_client = storage.Client()

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket_name)

    for blob in blobs:
        print(blob.name)


def list_blobs_with_prefix(bucket_name, prefix, delimiter=None):
    """Lists all the blobs in the bucket that begin with the prefix.

    This can be used to list all blobs in a "folder", e.g. "public/".

    The delimiter argument can be used to restrict the results to only the
    "files" in the given "folder". Without the delimiter, the entire tree under
    the prefix is returned. For example, given these blobs:

        a/1.txt
        a/b/2.txt

    If you just specify prefix = 'a', you'll get back:

        a/1.txt
        a/b/2.txt

    However, if you specify prefix='a' and delimiter='/', you'll get back:

        a/1.txt

    Additionally, the same request will return blobs.prefixes populated with:

        a/b/
    """

    storage_client = storage.Client()

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket_name, prefix=prefix, delimiter=delimiter)

    print("Blobs:")
    for blob in blobs:
        print(blob.name)

    if delimiter:
        print("Prefixes:")
        for prefix in blobs.prefixes:
            print(prefix)
