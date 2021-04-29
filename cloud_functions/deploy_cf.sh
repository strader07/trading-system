#!/bin/bash

gcloud functions deploy om-analytics \
--project strange-metrics-258802 \
--region europe-west2 \
--runtime python37 \
--entry-point main \
--trigger-resource gs://om_analytics \
--trigger-event google.storage.object.finalize
