from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import col, lit, year, month, dayofmonth
import os
import sys
import json
from util import get_start_date, bbo_imbalance, book_imbalance, convert_name
# CLI command:
# gcloud dataproc jobs submit pyspark --cluster [cluster_name] dataproc_book_raw_to_intermediate.py\
# --py-files util.py --files symbols.json -- [initial-load / delta-load]

with open('symbols.json') as f:
    symbols = json.load(f)['symbols']

load_type = sys.argv[1]

spark = SparkSession.builder.appName("book_raw_to_intermediate").getOrCreate()
spark.conf.set("spark.sql.sources.partitionOverwriteMode","dynamic")
output_bucket = "gs://intermediate_mktdata"
in_paths = [f'gs://raw_mktdata/book/ftx/{x}/*/*/*/*' for x in symbols]
intermediate_paths = [f'gs://intermediate_mktdata/book/exchange=ftx/symbol={x}/*/*/*/*' for x in symbols]

start_date = get_start_date(load_type, 'gs://intermediate_mktdata/book/', intermediate_paths, spark)

df = spark.read.parquet(*in_paths)
df = df.where(df.time >= start_date)

df = df.withColumn('spread', df.AskPrice0 - df.BidPrice0) \
		.withColumn('midprice', (df.AskPrice0 + df.BidPrice0)/2) \
		.withColumn('bbo_imbalance', bbo_imbalance(df.BidSize0, df.AskSize0)) \
		.withColumn('book_imbalance', book_imbalance(df)) \
		.withColumn("year", year(df.time)) \
		.withColumn("month", month(df.time)) \
		.withColumn("day", dayofmonth(df.time))

df = convert_name(df)
df = df.withColumnRenamed("time", "timestamp")

df.write.mode('overwrite').partitionBy('exchange', 'symbol', 'year', 'month', 'day') \
								.parquet(f'{output_bucket}/book/')