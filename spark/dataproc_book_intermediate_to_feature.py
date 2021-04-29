from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import col, lit, year, month, dayofmonth, count, stddev, mean
import sys
import json
from util import resample, get_start_date

# CLI command:
# gcloud dataproc jobs submit pyspark --cluster [cluster_name] dataproc_book_intermediate_to_feature.py\
# --py-files util.py --files symbols.json -- [initial-load / delta-load]

with open('symbols.json') as f:
    symbols = json.load(f)['symbols']

load_type = sys.argv[1]

spark = SparkSession.builder.appName("book_intermediate_to_feature").getOrCreate()
spark.conf.set("spark.sql.sources.partitionOverwriteMode","dynamic")
output_bucket = "gs://features_mktdata"
in_paths = [f'gs://intermediate_mktdata/book/exchange=ftx/symbol={x}/*/*/*/*' for x in symbols]
feature_paths = [f'gs://features_mktdata/book/exchange=ftx/symbol={x}/*/*/*/*' for x in symbols]

start_date = get_start_date(load_type, f'{output_bucket}/book/', feature_paths, spark)

df = spark.read.option("basePath", 'gs://intermediate_mktdata/book/').parquet(*in_paths)
df = df.where(df.timestamp >= start_date)

resample_buckets = [10, 30, 60]

for sec_bucket in resample_buckets:
	df = df.withColumn(f'dt_resampled_{sec_bucket}s', resample(df.timestamp, agg_interval=sec_bucket))

for sec_bucket in resample_buckets:
	df_agg = df.groupby('exchange', 'symbol', f'dt_resampled_{sec_bucket}s') \
		.agg(
			count(f'dt_resampled_{sec_bucket}s').alias('count_events'),
			mean('spread').alias('spread_mean'),
			stddev('spread').alias('spread_std'),
			mean('midprice').alias('midprice_mean'),
			stddev('midprice').alias('midprice_std'),
			mean('bbo_imbalance').alias('bbo_imbalance_mean'),
			stddev('bbo_imbalance').alias('bbo_imbalance_std'),
			mean('book_imbalance').alias('book_imbalance_mean'),
			stddev('book_imbalance').alias('book_imbalance_std'),
	).sort(f'dt_resampled_{sec_bucket}s')

	df_agg = df_agg.withColumnRenamed(f"dt_resampled_{sec_bucket}s", "timestamp")

	df_agg = df_agg.withColumn("year", year(df_agg.timestamp)) \
					.withColumn("month", month(df_agg.timestamp)) \
					.withColumn("day", dayofmonth(df_agg.timestamp)) \
					.withColumn("bucket_size", lit(f"{sec_bucket}_second_bucketing"))

	df_agg.write.mode('overwrite')\
				.partitionBy('exchange', 'symbol', 'bucket_size', 'year', 'month', 'day')\
				.parquet(f"{output_bucket}/book/")

