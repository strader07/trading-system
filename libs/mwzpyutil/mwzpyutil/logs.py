import logging
import sys
from pythonjsonlogger import jsonlogger


class _MaxLevelFilter:
    def __init__(self, highest_log_level):
        self._highest_log_level = highest_log_level

    def filter(self, log_record):
        return log_record.levelno <= self._highest_log_level


class StackDriverJsonFormatter(jsonlogger.JsonFormatter):
    def __init__(self, fmt="%(levelname) %(message)", style="%", *args, **kwargs):
        jsonlogger.JsonFormatter.__init__(self, fmt=fmt, *args, **kwargs)

    def process_log_record(self, log_record):
        log_record["severity"] = log_record["levelname"]
        del log_record["levelname"]
        return super().process_log_record(log_record)


# JSON formatter
formatter = StackDriverJsonFormatter()

# A handler for low level logs that should be sent to STDOUT
info_handler = logging.StreamHandler(sys.stdout)
info_handler.setFormatter(formatter)
info_handler.setLevel(logging.INFO)
info_handler.addFilter(_MaxLevelFilter(logging.WARNING))

# A handler for high level logs that should be sent to STDERR
error_handler = logging.StreamHandler(sys.stderr)
error_handler.setFormatter(formatter)
error_handler.setLevel(logging.ERROR)

logger = logging.getLogger()
# logger default level is WARNING, so we'll override to be INFO.
logger.setLevel(logging.INFO)
logger.addHandler(info_handler)
logger.addHandler(error_handler)
