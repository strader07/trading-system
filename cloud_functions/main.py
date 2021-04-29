import os
import logging
from typing import List
from latency import get_data
from google.cloud.bigquery.table import Table, TableReference
from google.cloud import storage

GCP_PROJECT = os.environ["GCP_PROJECT"]
TMP_FOLDER = "/tmp"


def load_gcs_file(bucket_name: str, file_name: str):
    """
    Downloads file from a Cloud Storage Bucket to local file
    :param bucket_name: name of Cloud Storage bucket
    :param file_name: file name (path) in bucket
    :return:
    """
    logging.info(f"downloading file {file_name}")
    gcs = storage.Client(project=GCP_PROJECT)
    bucket = gcs.bucket(bucket_name)
    blob = bucket.blob(file_name)
    output_filepath = os.path.join(TMP_FOLDER, file_name)
    blob.download_to_filename(output_filepath)
    return output_filepath


def bq_insert(rows: List):
    """
    Inserts rows into BigQuery
    :param rows: list of dictionaries which are representing rows
    :return:
    """
    from google.cloud import bigquery

    if not rows:
        logging.error("no rows to upload")
        return
    bq = bigquery.Client(project=GCP_PROJECT)
    table_ref = TableReference.from_string(f"{GCP_PROJECT}.live.om_state_latencies")

    schema = [
        {"name": "date", "type": "DATE"},
        {"name": "sym", "type": "STRING"},
        {"name": "from_state", "type": "STRING"},
        {"name": "to_state", "type": "STRING"},
        {"name": "count", "type": "INTEGER"},
        {"name": "average", "type": "FLOAT"},
        {"name": "percentile_10", "type": "FLOAT"},
        {"name": "percentile_50", "type": "FLOAT"},
        {"name": "percentile_90", "type": "FLOAT"},
        {"name": "percentile_99", "type": "FLOAT"},
        {"name": "percentile_99_99", "type": "FLOAT"},
    ]

    table = Table(table_ref)
    table.schema = schema
    table = bq.create_table(table, exists_ok=True)
    logging.info("inserting {} rows".format(len(rows)))
    res = bq.insert_rows(table, rows)
    logging.info(res)


def delete_file(file_name):
    """Deletes downloaded file
    :param file_name: name of local file
    """
    file_path = os.path.join(TMP_FOLDER, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)


def process(bucket_name, file_name):
    """Step executed"""
    file_path = load_gcs_file(bucket_name, file_name)
    data = get_data(file_path)
    bq_insert(data)
    delete_file(file_name)


def main(data, context=None):
    bucket_name = data["bucket"]
    file_name = data["name"]
    logging.info(f"receiving file: {file_name} from bucket {bucket_name}")
    process(bucket_name, file_name)


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
