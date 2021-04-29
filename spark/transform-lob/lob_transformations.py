import pyspark # only run after findspark.init()
from pyspark.sql import SparkSession
from pyspark.sql import functions as func
from pyspark.sql.window import Window
from pyspark.sql.functions import array, col, explode, lit, struct, split, mean, stddev, lead, lag, concat, count, year, month, dayofmonth
from pyspark.sql import DataFrame
from typing import Iterable 
from pyspark.sql.types import IntegerType
from pyspark.sql.functions import broadcast
from datetime import datetime
from util import *

# TODO: Point to appropriate spark server
spark = SparkSession.builder.config("spark.driver.memory", "16g")\
							.config("spark.driver.maxResultSize", "1g")\
							.config("spark.sql.sources.partitionOverwriteMode", "dynamic")\
							.getOrCreate()

def lob_raw_to_intermediate(exchange, symbol, root_data_path='data'):
	# TODO: Make date dynamic, depending on how we choose to refresh
	df = spark.read.format('com.databricks.spark.csv').options(header='true', inferschema='true') \
	.load(f'{root_data_path}/01_raw/lob/{exchange}/{symbol}/2019/*/*')

	# Clean column names
	# TODO: Adjust to our data
	for col in df.columns:
		df = df.withColumnRenamed(col, col.replace('.', '').replace(']', '').replace('[', ''))

	df = df.withColumn('spread', df.asks0price - df.bids0price) \
		.withColumn('midprice', (df.asks0price + df.bids0price)/2) \
		.withColumn('bbo_imbalance', bbo_imbalance(df.bids0amount, df.asks0amount)) \
		.withColumn('book_imbalance', book_imbalance(df)) \
		.withColumn("year", year(df.timestamp)) \
		.withColumn("month", month(df.timestamp)) \
		.withColumn("day", dayofmonth(df.timestamp))\
		.withColumn("exchange", lit(exchange))

	df.write.mode('overwrite').partitionBy('exchange', 'symbol', 'year', 'month', 'day') \
								.parquet(f"{root_data_path}/02_intermediate/lob")


def lob_intermediate_to_feature(exchange, symbol, root_data_path='data'):
	resample_buckets = [10, 30, 60]

	# TODO: Make date dynamic, depending on how we choose to refresh
	df = spark.read.load(f'{root_data_path}/02_intermediate/lob/exchange={exchange}/symbol={symbol}/year=2019/*/*')

	for sec_bucket in resample_buckets:
		df = df.withColumn(f'dt_resampled_{sec_bucket}s', resample(df.timestamp, agg_interval=sec_bucket))

	for sec_bucket in resample_buckets:
		df_agg = df.groupby(f'dt_resampled_{sec_bucket}s') \
			.agg(
				count(f'dt_resampled_{sec_bucket}s'),
				mean('spread'),
				stddev('spread'),
				mean('midprice'),
				stddev('midprice'),
				mean('bbo_imbalance'),
				stddev('bbo_imbalance'),
				mean('book_imbalance'),
				stddev('book_imbalance'),
		).sort(f'dt_resampled_{sec_bucket}s')

		df_agg = df_agg.withColumnRenamed(f"dt_resampled_{sec_bucket}s", "timestamp") \
						.withColumnRenamed(f"count(dt_resampled_{sec_bucket}s)", "count_events") \
						.withColumnRenamed("avg(spread)", "spread_mean") \
						.withColumnRenamed("stddev_samp(spread)", "spread_std") \
						.withColumnRenamed("avg(midprice)", "midprice_mean") \
						.withColumnRenamed("stddev_samp(midprice)", "midprice_std") \
						.withColumnRenamed("avg(bbo_imbalance)", "bbo_imbalance_mean") \
						.withColumnRenamed("stddev_samp(bbo_imbalance)", "bbo_imbalance_std") \
						.withColumnRenamed("avg(book_imbalance)", "book_imbalance_mean") \
						.withColumnRenamed("stddev_samp(book_imbalance)", "book_imbalance_std") 

		df_agg = df_agg.withColumn('exchange', lit(exchange)) \
						.withColumn('symbol', lit(symbol)) \
						.withColumn("year", year(df_agg.timestamp)) \
						.withColumn("month", month(df_agg.timestamp)) \
						.withColumn("day", dayofmonth(df_agg.timestamp)) \
						.withColumn("bucket_size", lit(f"{sec_bucket}_second_bucketing"))

		df_agg.write.mode('overwrite').partitionBy('exchange', 'symbol', 'bucket_size', 'year', 'month', 'day') \
										.parquet("{root_data_path}/03_feature/lob")
