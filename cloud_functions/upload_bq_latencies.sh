#!/bin/bash


BUCKET=om_analytics_test
INPUT_FILENAME=latencies.csv
GCS_PATH=gs://$BUCKET/$INPUT_FILENAME
DATASET=live
TABLE=om_state_latencies_test

bq load \
--source_format=CSV \
--skip_leading_rows=1 \
strange-metrics-258802:$DATASET.$TABLE \
$GCS_PATH \
date:DATE,sym:STRING,from_state:STRING,to_state:STRING,count:INTEGER,average:FLOAT,percentile_10:FLOAT,percentile_50:FLOAT,percentile_90:FLOAT,percentile_99:FLOAT,percentile_99_99:FLOAT