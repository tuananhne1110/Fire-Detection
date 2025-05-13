import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from dotenv import load_dotenv

load_dotenv()
service = os.getenv("SERVICE")
# Disable all logging for MinIO and urllib3
logging.getLogger("minio").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("kafka").setLevel(logging.CRITICAL)


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;21m "
    yellow = "\x1b[33;21m "
    red = "\x1b[31;21m "
    bold_red = "\x1b[31;1m "
    reset = " \x1b[0m"

    format = "%(asctime)s %(levelname)8s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


class SizedAndTimedRotatingHandler(TimedRotatingFileHandler):
    def __init__(
        self,
        filename,
        when="h",
        interval=1,
        maxBytes=0,
        backupCount=5,
        encoding=None,
        delay=False,
        utc=False,
        atTime=None,
    ):
        self._max_bytes = maxBytes
        TimedRotatingFileHandler.__init__(
            self,
            filename,
            when=when,
            interval=interval,
            backupCount=backupCount,
            encoding=encoding,
            delay=delay,
            utc=utc,
            atTime=atTime,
        )
        self.backup_count = backupCount

    def shouldRolloverOnSize(self):
        if os.path.exists(self.baseFilename) and not os.path.isfile(self.baseFilename):
            return False

        if self.stream is None:
            return False

        if self._max_bytes > 0:
            self.stream.seek(0, 2)
            if self.stream.tell() >= self._max_bytes:
                return True
        return False

    def shouldRollover(self, record):
        return self.shouldRolloverOnSize() or super().shouldRollover(record)

    def getFilesToDelete(self):
        dir_name, base_name = os.path.split(self.baseFilename)
        files_dict = {}
        for fileName in os.listdir(dir_name):
            _, ext = os.path.splitext(fileName)
            date_str = ext.replace(".", "")
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")
                files_dict[d] = fileName
            except:
                pass
        if len(files_dict) < self.backup_count:
            return []

        sorted_dict = dict(sorted(files_dict.items(), reverse=True))
        return [os.path.join(dir_name, v) for k, v in sorted_dict.items()][
            self.backup_count :
        ]


def init_logger():
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    os.makedirs(f"logs/{service}", exist_ok=True)
    log_file = f"logs/{service}/log.log"
    max_log_size = 5 * 1024 * 1024

    handler = SizedAndTimedRotatingHandler(
        log_file, maxBytes=max_log_size, backupCount=7, when="midnight"
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(CustomFormatter())

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(CustomFormatter())

    logger.addHandler(stream_handler)
    logger.addHandler(handler)
    return logger


logger = init_logger()
