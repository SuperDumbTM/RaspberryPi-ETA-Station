import os
import sys
from abc import ABC, abstractmethod
from PIL import ImageFont
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
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
    
    def __init__(self, root: str, size: int) -> None:
        self.logger.debug(f"Initializing class {self.__class__.__name__}")
        self.root = root
        
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
        self.logger.debug("reading epd.conf")
        self.parser = _configparser.ConfigParser(os.path.join(root, "conf", "eta.conf"))
        self.parser.read()
        self.conf = self.parser.get_conf()
        
        # font
        self.logger.debug("setting up font")
        font_dir = os.path.join(root, "font")
        self.f_route = ImageFont.truetype(os.path.join(font_dir, "superstar_memesbruh03.ttf"), self.lyo['f_route'])
        self.f_text = ImageFont.truetype(os.path.join(font_dir, "msjh.ttc"), self.lyo['f_text'])
        self.f_time = ImageFont.truetype(os.path.join(font_dir, "agencyb.tff"), self.lyo['f_time'])
        self.f_mins = ImageFont.truetype(os.path.join(font_dir, "GenJyuuGothic-Monospace-Medium.ttf"), self.lyo['f_mins'])
        self.f_min = ImageFont.truetype(os.path.join(font_dir, "GenJyuuGothic-Monospace-Regular.ttf"), self.lyo['f_min'])
        self.f_lmins = ImageFont.truetype(os.path.join(font_dir, "GenJyuuGothic-Monospace-Medium.ttf"), self.lyo['f_lmins'])
    
    def can_partial(self) -> bool:
        return self.partial

    def set_mode(self, mode):
        self.mode = mode
    
    @staticmethod
    @abstractmethod
    def can_partial() -> bool:
        pass
    
    @abstractmethod
    def init(self):
        self.logger.info("Initializing the e-paper")

    @abstractmethod
    def clear(self):
        self.logger.debug("Clearing the e-paper")

    def exit(self):
        self.logger.info("Powering down the e-paper")
        self.epd.sleep()
    
    @abstractmethod
    def draw(self):
        self.logger.info("Drawing ETAs")

    @abstractmethod
    def full_update(self, deg: int):
        self.logger.debug("Refreshing the display in full update mode")

    def partial_update(self, deg: int, intv: int, times: int, mode: str, img_path: str):
        '''
        partial update only available when e-paper display is supported
        
        @args
            - `deg`: Angle for diplay output rotation
            - `intv`: Time in second for partial update period (loop mode)
            - `times`: looping time (loop mode)
            - `mode`: {loop, mode}
                - [loop] a full update follow by `times` - 1 partial update with interval `intv`
                - [normal] one partial update only, require a previous output image to work
            - `img_path`: path to previous display output image file for (normal mode)
        '''
        self.logger.debug("Refreshing the display in partial update mode")

    def save_image(self, path: str):
        if os.path.exists(os.path.dirname(path)):
            self.img.save(path)
        else:
            self.logger.warning(f"{path} do not exits, saving the image to tmp/output.bmp")
            self.img.save(self.root, "tmp", "output.bmp")
