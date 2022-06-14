import os
import sys
from abc import ABC, abstractmethod
from PIL import Image,ImageDraw,ImageFont
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) # lib path
from src.config import _configparser
from src.log.mylogger import Logger

class DisplayABC:
    
    partial: bool
    epd_height: int
    epd_width: int
    black: int
    white: int
    
    LAYOUT: dict
    logger = Logger.log
    
    def __init__(self, size: int) -> None:
        self.logger.debug(f"Initializing class {self.__class__.__name__}")
        self.__path_check()
        
        if size > 3:
            self.num_etas = 3
            self.logger.warning("supplied display size is not supported, fallback to 3")
        else :
            self.num_etas = size
            self.logger.debug(f"display size is set to {self.num_etas}")
            
        if self.num_etas == 1:
            self.lyo = self.LAYOUT[1]
        elif self.num_etas == 2:
            self.lyo = self.LAYOUT[2]
        else:
            self.lyo = self.LAYOUT[3]
        
        # conf  
        self.logger.debug("reading conf/epd.conf")
        self.parser = _configparser.ConfigParser("conf/eta.conf")
        self.parser.read()
        self.conf = self.parser.get_conf()
        
        # font
        self.logger.debug("setting up font")
        self.f_route = ImageFont.truetype("./font/superstar_memesbruh03.ttf", self.lyo['f_route'])
        self.f_text = ImageFont.truetype("./font/msjh.ttc", self.lyo['f_text'])
        self.f_time = ImageFont.truetype("./font/agencyb.tff", self.lyo['f_time'])
        self.f_mins = ImageFont.truetype("./font/GenJyuuGothic-Monospace-Medium.ttf", self.lyo['f_mins'])
        self.f_min = ImageFont.truetype("./font/GenJyuuGothic-Monospace-Regular.ttf", self.lyo['f_min'])
        self.f_lmins = ImageFont.truetype("./font/GenJyuuGothic-Monospace-Medium.ttf", self.lyo['f_lmins'])
    
    def can_partial(self) -> bool:
        return self.partial
    
    def __path_check(self):
        if not os.path.exists("conf/epd.conf"):
            self.logger.critical("epd.conf is missing")
            raise FileNotFoundError()
        if not os.path.exists("conf/eta.conf"):
            self.logger.critical("epd.conf is missing")
            raise FileNotFoundError("eta.conf")
        if not os.path.exists("font/"):
            self.logger.critical("font/ is missing")
            raise FileNotFoundError()
        if not os.path.exists("data/"):
            self.logger.warning("data/ is missing")
            os.makedirs("data/")
            os.makedirs("data/route_data")
            os.makedirs("data/route_data/kmb")
            os.makedirs("data/route_data/mtr")
            os.makedirs("data/route_data/mtr/bus")
            os.makedirs("data/route_data/mtr/bus/lrt")

    def set_mode(self, mode):
        self.mode = mode
    
    @staticmethod
    @abstractmethod
    def can_partial():
        pass
    
    @abstractmethod
    def init(self):
        self.logger.info("Initializing the e-paper")

    @abstractmethod
    def clear(self):
        self.logger.debug("Clearing the e-paper")

    @abstractmethod
    def exit(self):
        self.logger.info("Powering down the e-paper")
    
    @abstractmethod
    def draw(self):
        self.logger.info("Drawing ETAs")

    @abstractmethod
    def full_update(self, deg: int):
        self.logger.debug("Refreshing the display in full update mode")

    @abstractmethod
    def partial_update(self, deg: int, intv: int, times: int):
        self.logger.debug("Refreshing the display in partial update mode")

    @abstractmethod
    def save_image(self):
        self.logger.debug("Saving the image output")