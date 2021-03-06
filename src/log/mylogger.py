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
    
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    
    
    def __init__(self) -> None:
        self.log = logging.getLogger('mylogger')
        self.log.setLevel(logging.DEBUG)
    
    def set_log_level(self, lv):
        self.log.setLevel(lv)
        self.log.debug(f"Updating log level")
        
    def verbose(self, lv):
        format = logging.Formatter('%(message)s', datefmt='%H:%M')
        
        ch = logging.StreamHandler()
        ch.setLevel(lv)
        ch.setFormatter(format)
        self.log.addHandler(ch)
    
    def add_file_logger(self, lv):
        filename = datetime.datetime.now().strftime("%Y%m%d.log")
        
        fh = logging.FileHandler(filename, mode='a')
        format = logging.Formatter('[%(levelname)s][%(asctime)s@%(module)s:%(lineno)d] %(message)s',
            datefmt='%H:%M:%S')
        fh.setLevel(lv)
        fh.setFormatter(format)
        self.log.addHandler(fh)