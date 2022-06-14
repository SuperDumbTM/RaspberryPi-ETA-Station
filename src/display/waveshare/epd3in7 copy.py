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

    def __init__(self, path: str,size: int) -> None:
        '''
        mode:
            - 0->4Gary mode
            - 1->1Gary mode
        '''
        self.row_h = 80
        self.row_size = 6       
        self.LAYOUT = LAYOUT
        super().__init__(path, size)
        
        if size > 3:
            self.num_etas = 3
        else :
            self.num_etas = size
            
        if self.num_etas == 1:
            self.lyo = LAYOUT[1]
        elif self.num_etas == 2:
            self.lyo = LAYOUT[2]
        else:
            self.lyo = LAYOUT[3]
            
        # obj
        self.img = Image.new('1', (EPD_WIDTH, EPD_HEIGHT), 255)
        self.drawing = ImageDraw.Draw(self.img)
        self.partial_upd = PARTIAL_UPD
        self.parser = _configparser.ConfigParser("conf/eta.conf")
        self.parser.read()
        self.conf = self.parser.get_conf()
        
        # constants
        self.black = GRAY4
        self.white = GRAY1
        # font
        self.f_route = ImageFont.truetype("./font/superstar_memesbruh03.ttf", self.lyo['f_route'])
        self.f_text = ImageFont.truetype("./font/msjh.ttc", self.lyo['f_text'])
        self.f_time = ImageFont.truetype("./font/agencyb.tff", self.lyo['f_time'])
        self.f_mins = ImageFont.truetype("./font/GenJyuuGothic-Monospace-Medium.ttf", self.lyo['f_mins'])
        self.f_min = ImageFont.truetype("./font/GenJyuuGothic-Monospace-Regular.ttf", self.lyo['f_min'])
        self.f_lmins = ImageFont.truetype("./font/GenJyuuGothic-Monospace-Medium.ttf", self.lyo['f_lmins'])
    
    def init(self, mode: int = 0):
        '''mode:
            - 0->4Gary mode
            - 1->1Gary mode
        '''
        super().init()

    def clear(self):
        super().clear()

    def exit(self):
        super().exit()
    
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
        
        for row, entry in enumerate(self.conf.values()):            
            _dets = dets.Details.get_obj(entry['eta_co'])(**entry)
            _eta = eta.Eta.get_obj(entry['eta_co'])(**entry)
            
            # route
            rte = entry['route']
            dest = _dets.get_dest()
            if not dest.lower().islower() and len(dest.translate(str.maketrans('', '', string.punctuation))) > 9:
                dest = dest[:9] + "..."
            elif dest.lower().islower() and len(dest) > 22:
                dest = dest[:21] + "..."
                
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
                            self.drawing.text((self.lyo['etax'], self.lyo['etay'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=eta_mins, fill=self.black, font=self.f_mins)
                            self.drawing.text((self.lyo['minx'], self.lyo['miny'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=self.lyo['min_desc'], fill=self.black, font=self.f_min)
                            self.drawing.text((self.lyo['timex'], self.lyo['timey'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=time['eta_time'], fill=self.black, font=self.f_time)
                        else:
                            self.drawing.text((self.lyo['lminx'], self.lyo['lminy'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=eta_mins, fill=GRAY4, font=self.f_lmins)
                    else: break

    def display_full(self):
        self.display_4Gray(self.getbuffer_4Gray(self.img))

    def exit(self):
        pass
        
CLS = Epd3in7