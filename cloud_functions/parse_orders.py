import csv
import sys
from collections import defaultdict

file_name = sys.argv[1]
filled_orders = []
orders_chrono = defaultdict(list)

def parse_file(f, func):
    with open(f) as f:
        csv_reader = csv.reader(f, delimiter=',')
        c = 0;
        for row in csv_reader:
            if c == 0:
                c += 1
                continue
            func(row)

def get_filled_orders(row):
    global filled_orders
    ordid = row[1]
    action = row[5]
    if action == 'fill':
        filled_orders.append(ordid)

def show_orders_chronology(row):
    ordid = row[1]
    action = row[5]
    if ordid in filled_orders:
        orders_chrono[ordid].append(row)

parse_file(file_name, get_filled_orders)
print(f'Filled orders: {filled_orders}\n')

attempted_cancel = 0

parse_file(file_name, show_orders_chronology)
for _id, events in orders_chrono.items():
    print(f'{_id}')
    for event in events:
        dt = event[0]
        action = event[5]
        if action == 'cancel' or action == 'mass_cancel':
            attempted_cancel += 1
        print(f'{dt} {action}')
    print('\n')

print(f'>>> Attempted cancel on {attempted_cancel}/{len(filled_orders)}\n')
