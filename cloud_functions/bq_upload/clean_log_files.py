import os
import csv
import io
import datetime
import sys

sys.path.insert(0, "../")

LOG_FOLDER = "aws_Logs"  # top folder with logs
OUTPUT_FOLDER = "clean_files"  # output folder where cleaned files are stored
ERRORS_FILE_PATH = 'errorsx.csv'  # file into which bad lines are written
OUTPUT_FILE_PATH = 'outputx.csv'  # output file into which all valid logs are written


# get all log files to process, ignore others
log_files = []
for dir_path, dir_names, filenames in os.walk(LOG_FOLDER):
    if "om.log" in filenames:
        full_path = os.path.join(dir_path, "om.log")
        log_files.append(full_path)


def get_strategy(line):
    assert len(line) >= 10
    if "USDT" in line[9]:
        strategy = "ftx_market_maker"
    else:
        strategy = "ftx_hedged_market_maker"
    return strategy


def clean_log_files():
    """
    1. cleans/reformat log file to correct structure / number of columns
    2. saves all content into one big file OUTPUT_FILE_PATH which is used for BigQuery upload
    3. saves every log file into OUTPUT_FOLDER keeping the same subfolder structure, this is
    used to extract latencies
    """
    
    with open(ERRORS_FILE_PATH, "w") as fe, open(OUTPUT_FILE_PATH, "w") as fo:
        csv_error = csv.writer(fe)
        csv_writer = csv.writer(fo)
        for log_file_path in log_files:
            print(log_file_path)
            out_file_path = log_file_path.replace(LOG_FOLDER, OUTPUT_FOLDER)
            out_file_folder = "/".join(out_file_path.split("/")[:-1])
            if not os.path.exists(out_file_folder):
                os.makedirs(out_file_folder)
            with open(log_file_path, "r") as f, open(out_file_path, "w") as fo_log:
                csv_log_writer = csv.writer(fo_log)
                file_content = f.read()
                file_content = file_content.replace("\x00", "")  # some files have NULL byte
                f_obj = io.StringIO(file_content)
                csv_reader = csv.reader(f_obj)
                line_no = 1
                for line in csv_reader:
                    line_len = len(line)
                    line_str = ",".join(line)
                    if "reject" in line_str:  # skip rejected since they are messed up
                        continue
                    if line_len < 2:  # skip 1 column, so I can check second column value
                        line.insert(0, log_file_path)
                        line.insert(0, line_no)
                        line.insert(0, line_len)
                        csv_error.writerow(line)
                        continue
                    if line[1] == "orderid":  # skip headers (first line)
                        continue
                    ts_str = line[0]
                    if "T" in ts_str:  # convert timestamp
                        ts_split = ts_str.split("T")
                        if len(ts_split) != 2:
                            continue
                        ts_date, ts_time = ts_split
                        ts_date_new = "{}-{}-{}".format(ts_date[0:4], ts_date[4:6], ts_date[6:])
                        ts_new = f"{ts_date_new} {ts_time}"
                        line[0] = ts_new
                    if line_len == 16:  # has extra column which is discarded
                        line = line[:-1]
                        csv_writer.writerow(line)
                        csv_log_writer.writerow(line)
                    elif line_len == 15:  # valid line
                        csv_writer.writerow(line)
                        csv_log_writer.writerow(line)
                    elif line_len == 14:  # missing strategy column
                        strategy = get_strategy(line)
                        line.append(strategy)
                        csv_writer.writerow(line)
                        csv_log_writer.writerow(line)
                    elif line_len == 13:  # missing 2 columns
                        strategy = get_strategy(line)
                        line.append("")
                        line.append(strategy)
                        csv_writer.writerow(line)
                        csv_log_writer.writerow(line)
                    else:  # non valid row
                        line.insert(0, log_file_path)
                        line.insert(0, line_no)
                        line.insert(0, line_len)
                        csv_error.writerow(line)

                    line_no += 1
                f_obj.close()


def get_latencies():
    """goes through all cleaned log files in output folder and extracts latencies
    and combines them into one file for BigQuery upload
    """

    from latency import get_data

    fieldnames = ("date", "sym", "from_state", "to_state", "count", "average", "percentile_10",
                  "percentile_50", "percentile_90", "percentile_99", "percentile_99_99")
    with open("latencies.csv", "w") as f_latencies:
        csv_writer = csv.DictWriter(f_latencies,
                                    fieldnames=fieldnames)
        csv_writer.writeheader()

        for dir_path, dir_names, filenames in os.walk(OUTPUT_FOLDER):
            for filename in filenames:
                full_path = os.path.join(dir_path, filename)
                print(full_path)
                with open(full_path) as f:
                    data = get_data(full_path)
                    if not data:
                        continue
                    for item in data:
                        csv_writer.writerow(item)


def validate():
    """just validate logs output file if columns number is correct and timestamps have correct format"""

    with open(OUTPUT_FOLDER) as f:
        csv_reader = csv.reader(f)
        c = 0
        for line in csv_reader:
            ts_str = line[0]
            try:
                datetime.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S.%f")
            except Exception:
                print(ts_str)
            if len(line) != 15:
                print(line)
        print(c)


if __name__ == "__main__":
    clean_log_files()
    validate()
    get_latencies()
