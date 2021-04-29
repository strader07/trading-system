#!/bin/bash

BUCKET=om_analytics
INPUT_FILENAME=om.csv
GCS_PATH=gs://$BUCKET/$INPUT_FILENAME
DATASET=live
TABLE=om_logs

bq load \
--source_format=CSV \
--skip_leading_rows=1 \
strange-metrics-258802:$DATASET.$TABLE \
$GCS_PATH \
ts:TIMESTAMP,orderid:INTEGER,price:FLOAT,size:FLOAT,fillqty:FLOAT,action:STRING,state:STRING,side:INTEGER,leavesqty:FLOAT,sym:STRING,ordtype:STRING,tif:STRING,execinst:STRING,rejreason:STRING,strategy:STRING
