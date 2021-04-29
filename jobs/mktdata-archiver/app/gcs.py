from mwzpyutil import logger
from google.cloud import storage


def store_file(settings, raw_file):
    base_dst = "{ftype}/{exchange}/{symbol}/{year}/{month}/{day}/{name}.parquet"
    dst = base_dst.format(
        ftype=raw_file.file_type.name.lower(),
        exchange=settings.market.exchange,
        symbol=settings.market.instrument,
        year=settings.date.year,
        month=settings.date.month,
        day=settings.date.day,
        name=f"{settings.market.instrument}_{settings.date}_{raw_file.file_type.name.lower()}",
    )

    storage_client = storage.Client()
    bucket = storage_client.bucket("raw_mktdata")
    blob = bucket.blob(dst)
    blob.upload_from_filename(raw_file.src)
    logger.info(f"Uploaded {settings}: {raw_file.src} -> {dst}")
