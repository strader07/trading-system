from pyspark.sql import functions as F
from datetime import timedelta
import dateutil.parser

cme_code = {
    "01": "F",
    "02": "G",
    "03": "H",
    "04": "J",
    "05": "K",
    "06": "M",
    "07": "N",
    "08": "Q",
    "09": "U",
    "10": "V",
    "11": "X",
    "12": "Z",
}

def get_start_date(load_type, base_path, next_level_paths, spark):
	# Args
	if load_type == 'initial-load':
		return '2019-01-01'
	elif load_type == 'delta-load':
		# Check the date of last update
		df_last = spark.read.option("basePath", base_path).parquet(*next_level_paths)
		df_last = df_last.groupby('exchange', 'symbol').agg(
			F.max("timestamp").alias("max_date"),
			F.min("timestamp").alias("min_date")
		)
		start_date = df_last.select(F.min('max_date')).first()[0]
		try:
			start_date = start_date - timedelta(days=1)
		except:
			start_date = dateutil.parser.parse(start_date) - timedelta(days=1)
		return start_date
	else:
		print('Incorrect load type argument')
		exit()

def resample(column, agg_interval=900, time_format='yyyy-MM-dd HH:mm:ss'):
	if type(column)==str:
		column = F.col(column)
	col_ut =  F.unix_timestamp(column, format=time_format)
	col_ut_agg =  F.floor(col_ut / agg_interval) * agg_interval  
	return F.from_unixtime(col_ut_agg)


def convert_name(df):
	split_col = F.split(df['symbol'], '-')
	df = df.withColumn('symbol_0', split_col.getItem(0))
	df = df.withColumn('symbol_1', \
		F.when(split_col.getItem(1) == 'PERP', 
			'USDP').otherwise(split_col.getItem(1).substr(0, 2))
		)
	df = df.replace(to_replace=cme_code, subset=['symbol_1'])
	df = df.withColumn('symbol', \
		F.when(df.symbol_1 == 'USDP', 
			F.concat(df.symbol_0, df.symbol_1)).otherwise(F.concat(df.symbol_0, df.symbol_1, F.lit('20')))
		)
	df = df.drop('symbol_0', 'symbol_1')
	return df

def bbo_imbalance(bid_size_0, ask_size_0):
	return bid_size_0 / (bid_size_0 + ask_size_0)

def book_imbalance(df):
	bid_cols = [x for x in df.columns if 'BidSize' in x]
	ask_cols = [x for x in df.columns if 'AskSize' in x]
	imb = sum(df[col] for col in df.columns if col in bid_cols) / \
				(sum(df[col] for col in df.columns if col in bid_cols) + sum(df[col] for col in df.columns if col in ask_cols))
	return imb