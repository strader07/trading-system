from datetime import datetime, timedelta, timezone


def date_str_to_timestamp(dt):
    return datetime.strptime(dt, "%Y%m%d-%H:%M:%S.%f").timestamp()


def date_from_str(dt):
    d = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
    return d.replace(tzinfo=timezone.utc)


def date_from_timestamp(ts):
    # return datetime.fromtimestamp(ts, timezone.utc)
    d = datetime.utcfromtimestamp(ts)
    return d.replace(tzinfo=timezone.utc)


def datetime_to_str(dt):
    dmin = dt.minute
    if dt.second > 0 or dt.microsecond > 0:
        dmin += 1
    ret = dt.replace(second=0, microsecond=0)
    return ret.strftime("%Y-%m-%dT%H:%M:%S")


def daterange(unit, start_date, end_date):
    delta = end_date - start_date
    if unit == "days":
        unit_delta = delta.days
    elif unit == "hours":
        unit_delta = delta.seconds / 3600
    elif unit == "minutes":
        unit_delta = delta.seconds / 60
    elif unit == "seconds":
        unit_delta = delta.seconds
    elif unit == "milliseconds":
        unit_delta = delta.seconds * 1000
    elif unit == "microseconds":
        unit_delta = delta.seconds * 1000000
    else:
        raise ValueError(f"Invalid timedelta unit: {unit}")

    arg = {unit: 0}
    for n in range(int(unit_delta) + 1):
        arg.update({unit: n})
        yield start_date + timedelta(**arg)
