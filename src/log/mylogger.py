import datetime
import logging
from typing import Literal

def singleton(cls):
    instances = {}
    def get_instance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return get_instance()

@singleton
class Logger:
    
    log: logging.Logger
    
    def __init__(self) -> None:
        self.log = logging.getLogger('root')
        self.log.setLevel(logging.DEBUG)

        # console out hander
        formatter_ch = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M')
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter_ch)
        self.log.addHandler(ch)
    
    def set_log_level(self, lv: Literal["debug","info","warning","error","critical"]):
        if lv == "debug":
            self.log.debug("Setting log level to <debug>")
            self.log.setLevel(logging.DEBUG)
        elif lv == "info":
            self.log.debug("Setting log level to <info>")
            self.log.setLevel(logging.INFO)
        elif lv == "warning":
            self.log.debug("Setting log level to <warning>")
            self.log.setLevel(logging.WARNING)
        elif lv == "error":
            self.log.debug("Setting log level to <error>")
            self.log.setLevel(logging.ERROR)
        elif lv == "critical":
            self.log.debug("Setting log level to <critical>")
            self.log.setLevel(logging.CRITICAL)
    
    def add_file_logger(self):
        log_filename = datetime.datetime.now().strftime("%Y%m%d.log")
        fh = logging.FileHandler(log_filename,mode='w+')
        formatter_fh = logging.Formatter('[%(levelname)s][%(asctime)s@%(module)s:%(lineno)d] %(message)s',
            datefmt='%Y%m%d|%H:%M:%S')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(self.formatter_ch)
        self.log.addHandler(fh)