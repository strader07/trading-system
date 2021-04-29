#!/bin/bash

echo "-> Starting upload_logs $(date)"

# Upload all logs to AWS

aws s3 sync --exclude 'flat/*' --only-show-errors /logs/ s3://trader-logs/
echo '-> Upload to AWS task done'

# Upload OM logs to Google for processing
mkdir -p /logs/flat
TODAY=`date +%Y%m%d`
mcp /logs/\*/\*/$TODAY/\*/om.log '/logs/flat/#1_#2_#3_om.csv'
mkdir -p /logs/errors
cd /logs/flat/
echo '-> Copied into /logs/flat'

echo '-> Deleting empty logs'
find . -type f -exec awk -v x=2 'NR==x{exit 1}' {} \; -exec echo rm -f {} \;
find . -type f -exec awk -v x=2 'NR==x{exit 1}' {} \; -exec rm -f {} \;

PROJECT=strange-metrics-258802
BUCKET=om_analytics
DATASET=live
TABLE=om_logs

gcloud config set project $PROJECT

export GOOGLE_APPLICATION_CREDENTIALS=/home/ubuntu/.cloudstorage-user.json

# Upload to Cloud Storage
echo '-> Uploading files to Cloud Storage'
for f in /logs/flat/*om.csv; do
    FILENAME=`basename $f`
    gsutil -m cp $FILENAME gs://$BUCKET/$FILENAME
    echo "  -> Uploaded $FILENAME"
done
echo '-> Cloud storage upload done'

# Upload to BigQuery
python3 /logs/upload_files_bq.py /logs/flat

echo '-> Gcloud upload done'

mv /logs/flat/bq_errors* /logs/errors

rm -rf /logs/flat

echo '-> /logs/flat cleared'

rm -rf /logs/f.*/$TODAY

echo '-> Cleared /logs/*/$TODAY'

echo "-> Done upload_logs $(date)"

echo '========================='
