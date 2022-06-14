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
        'f_time': 15,
        'f_mins': 18,
        'f_min': 18,
        'f_lmins': 14,
        'etax': 170,
        'etay': 2,
        'minsx': 190,
        'minsy': 2,
        'minx': 215,
        'miny': 5,
        'lminsx': 170,
        'lminsy': 5,
        'eta_pad': 25,
        'min_desc': "分"
    },
    # size = 6
    2:{
        'f_route': 40,
        'f_text': 16,
        'f_time': 15,
        'f_mins': 20,
        'f_min': 20,
        'f_lmins': 16,
        'etax': 170,
        'etay': 2,
        'minsx': 190,
        'minsy': 2,
        'minx': 230,
        'miny': 25,
        'lminsx': 170,
        'lminsy': 7,
        'eta_pad': 35,
        'min_desc': "分"
    },
    # size = 5
    1:{
        'f_route': 40,
        'f_text': 16,
        'f_time': 20,
        'f_mins': 25,
        'f_min': 25,
        'f_lmins': 14,
        'etax': 170,
        'etay': 10,
        'minsx': 200,
        'minsy': 10,
        'minx': 170,
        'miny': 40,
        'lminsx': 170,
        'lminsy': 25,
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

    def __init__(self, size: int) -> None:
        '''
        mode:
            - 0->4Gary mode
            - 1->1Gary mode
        '''
        self.row_h = 80
        self.row_size = 6       
        self.LAYOUT = LAYOUT
        super().__init__(size)
        
        
        
        # obj
        self.epd = epd.EPD()
        self.img = Image.new('1', (self.epd_width, self.epd_height), 255) # may need override
        self.drawing = ImageDraw.Draw(self.img)
    
    def init(self):
        self.epd.init(self.mode)  
        super().init()

    def clear(self):
        super().clear()
        self.epd.Clear(0xFF, self.mode)

    def exit(self):
        super().exit()
        self.epd.sleep()
        
    def full_update(self, deg: int):
        super().full_update(deg)
        self.epd.display_4Gray(self.epd.getbuffer_4Gray(self.img.rotate(deg)))

    @staticmethod
    def can_partial():
        return PARTIAL

    def partial_update(self, deg: int):
        super().partial_update(deg)
        
        _img = Image.new('1', (self.epd_width, self.epd_height), 255)
        ImageDraw.Draw(_img).rectangle((0, 150, self.epd_width, self.epd_height), fill = 255)
        self.epd.display_1Gray(self.epd.getbuffer(_img.rotate(deg)))
        time.sleep(0.3)
        self.epd.display_1Gray(self.epd.getbuffer(self.img.rotate(deg)))


    def draw(self):
        '''
        M: 
            route:  (5,5)
            dest:   (5,35)
            stop:   (5,55)
            
        '''
        super().draw()
        # Frame
        self.logger.debug("Drawing the frame")
        for row in range(self.row_size):
            self.drawing.line((0, self.row_h * (row+1), self.epd_height, 80 * (row+1)))
        
        # ETA
        self.logger.debug("Drawing ETA(s)")
        for row, entry in enumerate(self.conf.values()):
            if  self.row_size <= row: 
                self.logger.warning(f"Number of ETA entry in eta.conf ({len(self.conf)}) is larger than allowed display number.  Stoped at {row}.")
                break
            
            self.logger.info(f"Reading entry {entry}")
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
            self.logger.debug(f"Drawing row {row}'s route information")
            self.drawing.text((5, (self.row_h*row + 0)), text=rte, fill=self.black, font=self.f_route)
            self.drawing.text((5, (self.row_h*row + 35)), dest, fill=self.black, font=self.f_text)
            self.drawing.text((5, (self.row_h*row + 55)), f"@{stop}", fill=self.black, font=self.f_text)
            
            # time
            self.logger.debug(f"Drawing row {row}'s ETA time")
            if _eta.error:
                self.drawing.text((170, self.row_h*row + 25), text=_eta.msg, fill=self.black, font=self.f_text)
            else:
                for idx, time in enumerate(_eta.get_etas()):
                    if (idx < 3):
                        eta_mins = str(time['eta_mins'])
                        if len(eta_mins) <= 3 :
                            self.drawing.text((self.lyo['etax'], self.lyo['etay'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=eta_mins, fill=self.black, font=self.f_mins)
                            self.drawing.text((self.lyo['minsx'], self.lyo['minsy'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=self.lyo['min_desc'], fill=self.black, font=self.f_min)
                            self.drawing.text((self.lyo['minx'], self.lyo['miny'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=time['eta_time'], fill=self.black, font=self.f_time)
                        else:
                            self.drawing.text((self.lyo['lminsx'], self.lyo['lminsy'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=eta_mins, fill=self.black, font=self.f_lmins)
                    else: break

    def save_image(self):
        super().save_image()
        self.img.save("tmp/output.bmp")


CLS = Epd3in7