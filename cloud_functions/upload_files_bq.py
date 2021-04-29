#!/usr/bin/env python

"""
Upload files *om.csv files in input folder to BigQuery
usage:
./upload_files_bq.py <input folder>
for example
./upload_files_bq.py /logs/flat/

"""

import os
import sys
import datetime
import logging
import warnings

from google.cloud import bigquery

GCP_PROJECT = 'strange-metrics-258802'
BUCKET = 'om_analytics'  # Cloud Storage bucket where log data are stored

warnings.simplefilter("ignore")

logger = logging.getLogger('bq_uploader')


def upload(dataset_name, table_name, file_path):
    bq = bigquery.Client(project=GCP_PROJECT)
    table_path = f"{GCP_PROJECT}.{dataset_name}.{table_name}"

    schema = [
        {"name": "ts", "type": "TIMESTAMP"},
        {"name": "orderid", "type": "INTEGER"},
        {"name": "price", "type": "FLOAT"},
        {"name": "size", "type": "FLOAT"},
        {"name": "fillqty", "type": "FLOAT"},
        {"name": "action", "type": "STRING"},
        {"name": "state", "type": "STRING"},
        {"name": "side", "type": "INTEGER"},
        {"name": "leavesqty", "type": "FLOAT"},
        {"name": "sym", "type": "STRING"},
        {"name": "ordtype", "type": "STRING"},
        {"name": "tif", "type": "STRING"},
        {"name": "execinst", "type": "STRING"},
        {"name": "rejreason", "type": "STRING"},
        {"name": "strategy", "type": "STRING"},
    ]

    job_config = bigquery.LoadJobConfig()
    job_config.schema = schema
    job_config.skip_leading_rows = 1
    job_config.source_format = bigquery.SourceFormat.CSV
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND

    job = bq.load_table_from_uri([file_path], table_path, job_config=job_config)
    try:
        job.result()
    except Exception as e:
        err_str = job.errors
        error_msg = "{} \t {}".format(file_path, err_str)
        logger.error(error_msg)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stderr.write('Enter folder (absolute path) where logs for upload are \n')
        sys.exit(1)
    logs_folder = sys.argv[1]

    log_filename = 'bq_errors_{}.log'.format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh = logging.FileHandler(log_filename)
    fh.setLevel(logging.ERROR)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # BigQuery settings
    dataset_name = 'live'
    table_name = 'om_logs'

    filenames = os.listdir(logs_folder)

    for file_path in filenames:
        if 'om.csv' not in file_path:
            continue
        file_name = file_path.split('/')[-1]
        gcs_path = f"gs://{BUCKET}/{file_name}"
        upload(dataset_name, table_name, gcs_path)
