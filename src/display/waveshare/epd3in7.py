import os
import string
import sys
import time
from PIL import Image,ImageDraw,ImageFont
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) # lib path
sys.path.append(os.path.dirname(__file__)) # waveshare path
from config import _configparser
from display.interface import DisplayABC
from eta import details as dets
from eta import eta
from epd_lib import epd3in7 as epd

PARTIAL = True
LAYOUT = {
    # size = 8
    3:{
        'f_route': 40,
        'f_text': 16,
        'f_time': 25,
        'f_mins': 25,
        'f_min': 18,
        'f_lmins': 14,
        'etax': 170,
        'etay': 0,
        'minx': 200,
        'miny': 4,
        'timex': 225,
        'timey': 1,
        'lminx': 170,
        'lminy': 6,
        'eta_pad': 25,
        'min_desc': "分"
    },
    # size = 6
    2:{
        'f_route': 40,
        'f_text': 16,
        'f_time': 30,
        'f_mins': 33,
        'f_min': 20,
        'f_lmins': 16,
        'etax': 170,
        'etay': 0,
        'minx': 203,
        'miny': 10,
        'timex': 225,
        'timey': 5,
        'lminx': 170,
        'lminy': 12,
        'eta_pad': 35,
        'min_desc': "分"
    },
    # size = 5
    1:{
        'f_route': 40,
        'f_text': 16,
        'f_time': 40,
        'f_mins': 35,
        'f_min': 35,
        'f_lmins': 14,
        'etax': 170,
        'etay': 0,
        'minx': 205,
        'miny': 0,
        'timex': 170,
        'timey': 35,
        'lminx': 180,
        'lminy': 30,
        'eta_pad': 35,
        'min_desc': "分鐘"
    }
}

class Epd3in7(DisplayABC):
    
    mode = 0
    epd_height = epd.EPD_HEIGHT
    epd_width = epd.EPD_WIDTH
    black = epd.GRAY4
    white = epd.GRAY1

    def __init__(self, root: str,size: int) -> None:
        '''
        mode:
            - 0->4Gary mode
            - 1->1Gary mode
        '''
        self.row_h = 80
        self.row_size = 6       
        self.LAYOUT = LAYOUT
        self.mode = 1
        super().__init__(root, size)
        
        
        
        # obj
        self.epd = epd.EPD()
        self.img = Image.new('1', (self.epd_width, self.epd_height), 255)
        self.drawing = ImageDraw.Draw(self.img)
    
    def init(self):
        super().init()
        self.epd.init(self.mode)  

    def clear(self):
        super().clear()
        self.epd.Clear(0xFF, self.mode)
        
    def full_update(self, deg: int):
        super().full_update(deg)
        self.epd.display_4Gray(self.epd.getbuffer_4Gray(self.img.rotate(deg)))

    @staticmethod
    def can_partial():
        return PARTIAL

    def partial_update(self, deg: int, intv: int, times: int, mode: str, img_path: str):
        if mode == "loop":
            # loop mode
            super().full_update(deg)
            self.full_update(deg)
            while times > 1:
                self.exit()
                end = time.time()
                time.sleep(intv - (end - start))
                start = time.time()
                super().partial_update(deg, intv, times)
                prev_img = self.img
                self.img = Image.new('1', (self.epd_width, self.epd_height), 255)
                self.drawing = ImageDraw.Draw(self.img)
                
                self.init()
                self.epd.display_1Gray(self.epd.getbuffer(prev_img.rotate(deg)))
                self.draw()
                self.epd.display_1Gray(self.epd.getbuffer(self.img.rotate(deg)))
                
                times -= 1
        elif mode == "normal":
            # normal mode
            if os.path.exists(img_path):
                prev_img = Image.open(img_path)
                self.epd.display_1Gray(self.epd.getbuffer(prev_img.rotate(deg)))
                time.sleep(0.5)
                self.epd.display_1Gray(self.epd.getbuffer(self.img.rotate(deg)))
            else:
                self.logger.error("Image file for partial update do not exists.  No update is done.\n\
                    Please check the path or do a full update with flag -i first (optional: -I <path> to specify the path)")

    def draw(self):
        '''
        M: 
            route:  (5,5)
            dest:   (5,35)
            stop:   (5,55)
            
        '''
        super().draw()
        # Frame
        self.logger.debug("Drawing the layout")
        for row in range(self.row_size):
            self.drawing.line((0, self.row_h * (row+1), self.epd_height, 80 * (row+1)))
        
        # ETA
        self.logger.debug("Drawing ETA(s)")
        for row, entry in enumerate(self.conf.values()):
            if  self.row_size <= row: 
                self.logger.warning(f"Number of ETA entry in eta.conf ({len(self.conf)}) is larger than allowed display number.  Stoped at {row}.")
                break
            
            self.logger.debug(f"- Reading entry {entry}")
            _dets = dets.Details.get_obj(entry['eta_co'])(**entry)
            _eta = eta.Eta.get_obj(entry['eta_co'])(**entry)
            
            rte = entry['route']
            dest = _dets.get_dest()
            if not dest.lower().islower() and len(dest.translate(str.maketrans('', '', string.punctuation))) > 9:
                dest = dest[:9] + "..."
            elif dest.lower().islower() and len(dest) > 22:
                dest = dest[:21] + "..."
                
            stop = _dets.get_stop_name()
            
            # titles
            self.logger.debug(f"- Drawing row {row}'s route information")
            self.drawing.text((5, (self.row_h*row + 0)), text=rte, fill=self.black, font=self.f_route)
            self.drawing.text((5, (self.row_h*row + 35)), dest, fill=self.black, font=self.f_text)
            self.drawing.text((5, (self.row_h*row + 55)), f"@{stop}", fill=self.black, font=self.f_text)
            
            # time
            self.logger.debug(f"- Drawing row {row}'s ETA time")
            if _eta.error:
                self.drawing.text((170, self.row_h*row + 25), text=_eta.msg, fill=self.black, font=self.f_text)
            else:
                for idx, time in enumerate(_eta.get_etas()):
                    if (idx < 3):
                        eta_mins = str(time['eta_mins'])
                        if len(eta_mins) <= 3 :
                            self.drawing.text((self.lyo['etax'], self.lyo['etay'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=eta_mins, fill=self.black, font=self.f_mins)
                            self.drawing.text((self.lyo['minx'], self.lyo['miny'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=self.lyo['min_desc'], fill=self.black, font=self.f_min)
                            self.drawing.text((self.lyo['timex'], self.lyo['timey'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=time['eta_time'], fill=self.black, font=self.f_time)
                        else:
                            self.drawing.text((self.lyo['lminx'], self.lyo['lminy'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=eta_mins, fill=self.black, font=self.f_lmins)
                    else: break


CLS = Epd3in7