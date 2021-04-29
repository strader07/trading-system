## om.csv
This file contains our orders data per trader per run. We have many traders running (anywhere between 30-50/day). A new file is created by the trader every time it restarts. We stop traders once a day at 23:45 UTC and restart them at 00:10 UTC. However, some traders may bounce intraday. Note that the first line, we have a header row but instead of the word "date", its the actual date. We will replace that in the bash cron that process these files. This is due to our logger how it works.

## parse_orders.py
This shows you the list of orders per file and its state transitions. We don't want to do anything with it for now.

## avg.py
This file takes om.csv as an input and calculcates the latencies between orders state changes and outputs that. We want this to run on Cloud Functions and output the latencies to BigQuery.


# Tasks:

Task 1: Upload om.csv to BigQuery as is. Note that these traders run in AWS and not GCP. Please let me know how we can do that and create the right table in BigQuery for it.

Task 2: Setup avg.py in Cloud Functions, upload the om.csv file as input once a day (23:46 cron job) and output the results into BigQuery.

Task 3: Show us how to manually control these cloud functions: deploy, run etc...



# Development

`bq_upload/clean_log_files.py` - cleans and fixes log files in a folder

`upload_file_bq.sh` - uploads file to BigQuery, GCS_PATH variable should contain full path in Cloud Storage prefixed with 
gs://, for example gs://om_analytics/om.csv

`upload_file_gcs.sh` - uploads file to Cloud Storage, this should be self explanatory

`deploy_cf.sh` - deploys Cloud Function. there are several parameters like GCS bucket which will trigger it

`.gcloudignore` - list of files not to upload to Cloud Function

`requirements.txt` - list of dependencies for Cloud Function, needs to be deployed

`main.py` - main file containing code for Cloud Function

`ts_convert.py` - converts log file to correct format for BigQuery timestamp

`upload_bq_latencies.sh` - uploads file with all latencies into BigQuery

`upload_files_bq.py` - upload log files from a folder into BigQuery, used in cron

