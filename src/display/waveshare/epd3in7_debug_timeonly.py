import os
import string
import sys
from PIL import Image,ImageDraw,ImageFont
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) # lib path
# sys.path.append(os.path.dirname(__file__)) # waveshare path
from config import _configparser
from display.interface import DisplayABC
from eta import details as dets
from eta import eta

# layout
S_ROW = 8
M_ROW = 6
M_ROW_HEIGHT = 80
L_ROW = 5

MAXROW = 6
EPD_WIDTH       = 280
EPD_HEIGHT      = 480
PARTIAL_UPD = True
GRAY1  = 0xff #white
GRAY2  = 0xC0 #Close to white
GRAY3  = 0x80 #Close to black
GRAY4  = 0x00 #black

LAYOUT = {
    # size = 8
    3:{
        'f_route': 40,
        'f_text': 16,
        'f_time': 27,
        'f_mins': 18,
        'f_min': 18,
        'f_lmins': 14,
        'etax': 170,
        'etay': 2,
        'minsx': 190,
        'minsy': 2,
        'timex': 190,
        'timey': 1,
        'lminsx': 170,
        'lminsy': 6,
        'eta_pad': 24,
        'min_desc': "分"
    },
    # size = 6
    2:{
        'f_route': 40,
        'f_text': 16,
        'f_time': 42,
        'f_mins': 20,
        'f_min': 20,
        'f_lmins': 16,
        'etax': 170,
        'etay': 2,
        'minsx': 190,
        'minsy': 2,
        'timex': 170,
        'timey': 0,
        'lminsx': 170,
        'lminsy': 10,
        'eta_pad': 35,
        'min_desc': "分"
    },
    # size = 5
    1:{
        'f_route': 40,
        'f_text': 16,
        'f_time': 60,
        'f_mins': 25,
        'f_min': 25,
        'f_lmins': 14,
        'etax': 170,
        'etay': 10,
        'minsx': 200,
        'minsy': 10,
        'timex': 170,
        'timey': 3,
        'lminsx': 170,
        'lminsy': 30,
        'eta_pad': 35,
        'min_desc': "分鐘"
    }
}

class Epd3in7(DisplayABC):

    mode = 0
    epd_height = EPD_HEIGHT
    epd_width = EPD_WIDTH
    black = GRAY4
    white = GRAY1

    def __init__(self, root: str,size: int) -> None:
        '''
        mode:
            - 0->4Gary mode
            - 1->1Gary mode
        '''
        self.row_h = 80
        self.row_size = 6       
        self.LAYOUT = LAYOUT
        super().__init__(root, size)
            
        # obj
        self.img = Image.new('1', (EPD_WIDTH, EPD_HEIGHT), 255)
        self.drawing = ImageDraw.Draw(self.img)
    
    def draw(self):
        super().draw()
        '''
        M: 
            route:  (5,5)
            dest:   (5,35)
            stop:   (5,55)
            
        '''
        for row in range(5):
            self.drawing.line((0, self.row_h * (row+1), EPD_HEIGHT, 80 * (row+1)))
        
        for row, entry in enumerate(self.conf):            
            _dets = dets.Details.get_obj(entry['eta_co'])(**entry)
            _eta = eta.Eta.get_obj(entry['eta_co'])(**entry)
            
            # route
            rte = entry['route']
            dest = self.dotted(_dets.get_dest(), 9)
            stop = self.dotted(_dets.get_stop_name(), 9)
                
            stop = _dets.get_stop_name()
            
            # titles
            self.drawing.text((5, (self.row_h*row + 0)), text=rte, fill=self.black, font=self.f_route)
            self.drawing.text((5, (self.row_h*row + 35)), dest, fill=self.black, font=self.f_text)
            
            if len(stop.replace(" ", "")) <= 8:
                self.drawing.text((5, (self.row_h*row + 55)), f"@{stop}", fill=self.black, font=self.f_text)
            else:
                stop = stop[:8] + "..."
                self.drawing.text((5, (self.row_h*row + 55)), f"@{stop}", fill=self.black, font=self.f_text)
            
            # etas
            if _eta.error:
                self.drawing.text((170, self.row_h*row + 25), text=_eta.msg, fill=self.black, font=self.f_text)
            else:
                for idx, time in enumerate(_eta.get_etas()):
                    if (idx < self.num_etas):
                        eta_mins = str(time['eta_mins'])
                        if len(eta_mins) <= 3 :
                            self.drawing.text((self.lyo['timex'], self.lyo['timey'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=time['eta_time'], fill=GRAY4, font=self.f_time)
                            #self.drawing.text((self.lyo['etax'], self.lyo['etay'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=eta_mins, fill=GRAY4, font=self.f_mins)
                            #self.drawing.text((self.lyo['minsx'], self.lyo['minsy'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=self.lyo['min_desc'], fill=GRAY4, font=self.f_min)
                        else:
                            self.drawing.text((self.lyo['lminsx'], self.lyo['lminsy'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=eta_mins, fill=GRAY4, font=self.f_lmins)
                    else: break

    def partial_update(self, deg: int, intv: int, times: int, mode: str, img_path: str):
        if mode == "loop":
            # loop mode
            self.logger.debug("Partial update - loop mode")
        if mode == "normal":
            self.logger.debug("Partial update - normal mode")

    def full_update(self, deg: int):
        super().full_update(deg)
        
CLS = Epd3in7