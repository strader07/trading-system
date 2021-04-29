from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import col, lit, year, month, dayofmonth, when, stddev, mean, count, sum, split
from pyspark.sql.types import LongType, IntegerType, StringType, FloatType, StructField, StructType, BooleanType, TimestampType, DoubleType

import sys
import time
import json
from util import resample, convert_name, get_start_date

with open('symbols.json') as f:
    symbols = json.load(f)['symbols']

load_type = sys.argv[1]

# CLI command:
# gcloud dataproc jobs submit pyspark --cluster [cluster_name] dataproc_trades_raw_to_feature.py\
# --py-files util.py --files symbols.json -- [initial-load / delta-load]

# Declare schema so that specific columns can be read
schema = StructType([
		StructField("time", TimestampType(), True),
		StructField("exchange", StringType(), True),
		StructField("symbol", StringType(), True),
		StructField("trade_id", IntegerType(), True),
		StructField("price", DoubleType(), True),
		StructField("size", DoubleType(), True),
		StructField("side", StringType(), True),
		StructField("liquidation", BooleanType(), True),
		])
spark = SparkSession.builder.appName("trades_raw_to_feature").getOrCreate()
spark.conf.set("spark.sql.sources.partitionOverwriteMode","dynamic")
output_bucket = "gs://features_mktdata"
in_paths = [f'gs://raw_mktdata/trades/ftx/{x}/*/*/*/*' for x in symbols]
feature_paths = [f'gs://features_mktdata/trades/exchange=ftx/symbol={x}/*/*/*/*' for x in symbols]

start_date = get_start_date(load_type, 'gs://features_mktdata/trades/', feature_paths, spark)

# Read data, ignoring trade_id column due to type UINT
df = spark.read.schema(schema).parquet(*in_paths)
df = df.select("time", "exchange", "symbol", "trade_id", "price", "size", "side", "liquidation")\
		.where(df.time >= start_date)

df = df.withColumn("side", when(df.side == "buy", 0).otherwise(1))
df = df.withColumn("liquidation", when(df.side == True, 1).otherwise(0))

cnt_cond = lambda cond: F.sum(F.when(cond, 1).otherwise(0))

resample_buckets = [10, 30, 60]
for sec_bucket in resample_buckets:
	df = df.withColumn(f'dt_resampled_{sec_bucket}s', resample(df.time, agg_interval=sec_bucket))

for sec_bucket in resample_buckets:
	df_agg = df.groupby('exchange', 'symbol', f'dt_resampled_{sec_bucket}s') \
		.agg(
			count(f'dt_resampled_{sec_bucket}s').alias('trade_count'),
			mean('price').alias('price_mean'),
			stddev('price').alias('price_std'),
			mean('size').alias('size_mean'),
			stddev('size').alias('size_std'),
			sum('size').alias('size_sum'),
			mean('liquidation').alias('liquidation_mean'),
			stddev('liquidation').alias('liquidation_std'),
			count('liquidation').alias('liquidation_count'),
			mean('side').alias('side_mean'),
			count(when(col('side') == 0, True)).alias('buy_side_count'),
			count(when(col('side') == 1, True)).alias('ask_side_count'),

		) \
		.sort('exchange', 'symbol', f'dt_resampled_{sec_bucket}s')

	df_agg = df_agg.withColumnRenamed(f"dt_resampled_{sec_bucket}s", "timestamp")
		
	df_agg = df_agg.withColumn("year", year(col('timestamp'))) \
					.withColumn("month", month(col('timestamp'))) \
					.withColumn("day", dayofmonth(col('timestamp'))) \
					.withColumn("bucket_size", lit(f"{sec_bucket}_second_bucketing"))

	df_agg = convert_name(df_agg)

	df_agg.write.mode('overwrite')\
				.partitionBy('exchange', 'symbol', 'bucket_size', 'year', 'month', 'day')\
				.parquet(f"{output_bucket}/trades/")