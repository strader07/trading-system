import csv
import sys
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

import numpy as np


def normalize_us(t):
    unit = "us"
    if t > 1000:
        t /= 1000
        unit = "ms"
    elif t > 1000000:
        t /= 1000000
        unit = "s"
    t = round(t, 3)
    return f"{t:,}{unit}"


class Event:
    name = None
    entries = None

    @dataclass
    class Entry:
        ordid: int
        delta: float

    def __init__(self, name):
        self.name = name
        self.entries = []

    def add_entry(self, ordid, delta):
        entry = self.Entry(ordid, delta)
        self.entries.append(entry)

    def __len__(self):
        return len(self.entries)

    def average(self):
        deltas = [e.delta for e in self.entries]
        avg = np.average(deltas)
        if np.isnan(avg):
            return 0
        return avg

    def percentile(self, percent):
        deltas = [e.delta for e in self.entries]
        p = np.percentile(deltas, percent)
        return p


class Deltas:
    events = None

    def __init__(self):
        self.events = {}

    def new_event(self, key):
        event = Event(key)
        self.events[key] = event

    def add_event_entry(self, event, ordid, delta):
        self.events[event].add_entry(ordid, delta)

    def event_size(self, name):
        return len(self.events[name])

    def print_avg(self, event_name):
        avg = self.events[event_name].average()
        print(f"Avg: {normalize_us(avg)}")

    def get_avg(self, event_name):
        avg = self.events[event_name].average()
        avg = round(avg, 0)
        return avg

    def print_percentile(self, event_name, percent):
        event = self.events[event_name]
        p = event.percentile(percent)
        p = normalize_us(p)
        print(f"p{percent}: {p}: {int(percent / 100 * len(event)):,}")

    def get_percentile(self, event_name, percent):
        event = self.events[event_name]
        if not event.entries:
            return 0
        p = event.percentile(percent)
        # p = normalize_us(p)
        return round(p, 0)


def calculate_event_deltas(events, orders):
    deltas = Deltas()

    for event in events:
        deltas.new_event(event)

    for ordid, ord_events in orders.items():

        for event in events:
            event0_date = None
            event1_date = None

            for ord_event in ord_events:
                if ord_event["action"] == event[0]:
                    event0_date = ord_event["date"]
                elif ord_event["action"] == event[1]:
                    event1_date = ord_event["date"]

            if event0_date and event1_date:
                delta = (event1_date - event0_date).microseconds
                deltas.add_event_entry(event, ordid, delta)

    return deltas


def load_orders(file_name):
    orders = defaultdict(list)
    with open(file_name) as f:
        csv_reader = csv.reader(f, delimiter=",")
        c = 0
        for row in csv_reader:
            if c == 0:
                c += 1
                continue
            ordid, order_data = populate_orders(row)
            if ordid == -1:
                continue
            orders[ordid].append(order_data)
    return orders


def get_cell(file_name, idx):
    with open(file_name) as f:
        csv_reader = csv.reader(f, delimiter=",")
        c = 0
        for row in csv_reader:
            if c == 0:
                c += 1
                continue
            return row[idx]


def populate_orders(row):
    date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S.%f")
    ordid = int(row[1])
    action = row[5]
    state = row[6]

    return ordid, {"date": date, "ordid": ordid, "action": action, "state": state}


def get_data(file_name):
    """get required information for regarding latencies"""
    percentiles = [10, 50, 90, 99, 99.99]
    events = [
        ("new", "confirm_new"),
        ("new", "pending_mass_cancel"),
        ("pending_mass_cancel", "confirm_cxl"),
        ("pending_mass_cancel", "fill"),
    ]
    orders = load_orders(file_name)
    if not orders:
        return
    deltas = calculate_event_deltas(events, orders)

    try:
        date = datetime.strptime(get_cell(file_name, 0), "%Y-%m-%d %H:%M:%S.%f")
    except Exception as e:
        print("Error extracting date from file.")
        raise e
    finally:
        file_date = date.strftime("%Y-%m-%d")

    try:
        sym = get_cell(file_name, 9)
    except Exception as e:
        print("Error extracting symbol from file.")
        raise e

    data = []
    for e in events:
        from_state, to_state = e
        e_avg = deltas.get_avg(e)
        count = deltas.event_size(e)
        row = {
            "date": file_date,
            "sym": sym,
            "from_state": from_state,
            "to_state": to_state,
            "count": count,
            "average": e_avg,
        }
        for p in percentiles:
            p_value = deltas.get_percentile(e, p)
            p_str = str(p).replace(".", "_")
            p_name = f"percentile_{p_str}"
            row[p_name] = p_value
        data.append(row)
    return data


if __name__ == "__main__":
    file_name = sys.argv[1]
    d = get_data(file_name)
    print(d)
