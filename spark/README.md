TODO flesh out.

```bash
gcloud dataproc jobs submit pyspark --cluster mktdata-spark dataproc_lob_raw_to_intermediate.py
```

Template:
```bash
gcloud dataproc jobs submit pyspark --cluster ${CLUSTER_NAME}\
    --properties=spark.jars.packages=JohnSnowLabs:spark-nlp:2.0.8 \
    --driver-log-levels root=FATAL \
    topic_model.py \
    -- ${ARGUMENT}
```
