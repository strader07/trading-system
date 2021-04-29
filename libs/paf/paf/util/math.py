from pandas import Series


def get_pct_difference(num1, num2):
    series = Series([num1, num2])
    return series.pct_change().iloc[1]


def get_series_pct_difference(arr):
    series = Series(arr)
    return series.pct_change()
