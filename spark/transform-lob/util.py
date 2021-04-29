from pyspark.sql import functions as F

def resample(column, agg_interval=900, time_format='yyyy-MM-dd HH:mm:ss'):
	if type(column)==str:
		column = F.col(column)

	# Convert the timestamp to unix timestamp format.
	# Unix timestamp = number of seconds since 00:00:00 UTC, 1 January 1970.
	col_ut =  F.unix_timestamp(column, format=time_format)

	# Divide the time into dicrete intervals, by rounding. 
	col_ut_agg =  F.floor(col_ut / agg_interval) * agg_interval  

	# Convert to and return a human readable timestamp
	return F.from_unixtime(col_ut_agg)

def bbo_imbalance(bid_size_0, ask_size_0):
	return bid_size_0 / (bid_size_0 + ask_size_0)

def book_imbalance(df):
	bid_cols = [x for x in df.columns if 'bids' in x and 'amount' in x]
	ask_cols = [x for x in df.columns if 'ask' in x and 'amount' in x]
	imb = sum(df[col] for col in df.columns if col in bid_cols) / \
				(sum(df[col] for col in df.columns if col in bid_cols) + sum(df[col] for col in df.columns if col in ask_cols))
	return imb