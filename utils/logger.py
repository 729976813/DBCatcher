import os
import logging
from .timeshift import TimeShift

class Logger:

    def __init__(self, name, log_dir="./", log_file=""):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.log_file = os.path.join(log_dir, log_file)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        sh = logging.StreamHandler()
        self.logger.addHandler(sh)

    def _write_file(self, msg):
        with open(self.log_file, 'a+') as f:
            f.write(msg + '\n')

    def get_timestr(self):
        timestamp = TimeShift.get_current_stamp()
        date_str = TimeShift.stamp_to_local(timestamp)
        return date_str

    def warn(self, msg):
        msg = "%s[WARN] %s" % (self.get_timestr(), msg)
        self.logger.warning(msg)
        self._write_file(msg)

    def info(self, msg):
        msg = "%s[INFO] %s" % (self.get_timestr(), msg)
        # self.logger.info(msg)
        self._write_file(msg)

    def error(self, msg):
        msg = "%s[ERROR] %s" % (self.get_timestr(), msg)
        self.logger.error(msg)
        self._write_file(msg)
