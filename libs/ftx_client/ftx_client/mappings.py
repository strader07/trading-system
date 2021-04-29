import calendar
from datetime import date


def last_friday(dt: date):
    last_friday = max(
        week[calendar.FRIDAY] for week in calendar.monthcalendar(dt.year, dt.month)
    )
    return date(year, month, last_friday)


def last_monday(dt: date):
    last_monday = max(
        week[calendar.MONDAY] for week in calendar.monthcalendar(dt.year, dt.month)
    )
    return date(year, month, last_monday)


cme_code = {
    1: "F",
    2: "G",
    3: "H",
    4: "J",
    5: "K",
    6: "M",
    7: "N",
    8: "Q",
    9: "U",
    10: "V",
    11: "X",
    12: "Z",
}


def get_cme_contract_code(dt: date):
    return f"{cme_code[month]}{dt.strftime('%y')}"


mappings = {"-PERP": "USDP"}

for year in [2019, 2020, 2021]:
    for month in range(1, 13):
        dt = date(year, month, 1)

        # Friday futures
        last_friday_date = last_friday(dt)
        friday_ftx_fmt = "%m%d" if year == date.today().year else "%Y%m%d"
        friday_ftx_fmt = last_friday_date.strftime(friday_ftx_fmt)
        mappings[f"-{friday_ftx_fmt}"] = get_cme_contract_code(dt)

        # Monday futures
        last_monday_date = last_monday(dt)
        monday_ftx_fmt = "%m%d" if year == date.today().year else "%Y%m%d"
        monday_ftx_fmt = last_monday_date.strftime(monday_ftx_fmt)
        mappings[f"-{monday_ftx_fmt}"] = get_cme_contract_code(dt)
