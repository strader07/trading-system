import sys
import csv


def convert(file_name):
    """converts timestamps to adhere to BigQuery timestamp format plus other possible modifications.
    Saves output in different file
    """
    output_filename = 'ts_' + file_name.rsplit('.', maxsplit=1)[0] + '.csv'
    with open(file_name) as f, open(output_filename, 'w') as fo:
        csv_reader = csv.reader(f)
        csv_writer = csv.writer(fo)
        for line in csv_reader:
            ts = line[0]
            ts_split = ts.split('T')
            if len(ts_split) != 2:
                continue
            ts_date, ts_time = ts_split
            ts_date_new = '{}-{}-{}'.format(ts_date[0:4], ts_date[4:6], ts_date[6:])
            ts_new = f'{ts_date_new} {ts_time}'
            line[0] = ts_new
            strategy = ''
            line.append(strategy)
            csv_writer.writerow(line)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("please run this script with input filename as first parameter")
        sys.exit(1)
    file_name = sys.argv[1]
    convert(file_name)
