from importlib import import_module
import os
import string
import sys
from PIL import Image,ImageDraw,ImageFont
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) # lib path
from display.interface import DisplayABC
from eta import details as dets
from eta import eta

EPD_WIDTH       = 280
EPD_HEIGHT      = 480
PARTIAL_UPD = True
MAXROW = 6
GRAY1  = 0xff #white
GRAY2  = 0xC0 #Close to white
GRAY3  = 0x80 #Close to black
GRAY4  = 0x00 #black

class Epd3in7(DisplayABC):
    
    mode = 0
    epd_height = EPD_HEIGHT
    epd_width = EPD_WIDTH
    black = GRAY4
    white = GRAY1
    LAYOUT = {
    # size = 8
    3:{
        'f_route': 33,
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
        'f_route': 33,
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
        'f_route': 33,
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

    def __init__(self, root: str,size: int) -> None:
        '''
        mode:
            - 0->4Gary mode
            - 1->1Gary mode
        '''
        self.row_h = 80
        self.row_size = 6       
        super().__init__(root, size)
            
        # obj
        self.img = Image.new('1', (EPD_WIDTH, EPD_HEIGHT), 255)
        self.drawing = ImageDraw.Draw(self.img)

    
    def draw(self):
        super().draw()
        # Frame
        self.logger.debug("Drawing the layout")
        for row in range(self.row_size):
            self.drawing.line((0, self.row_h * (row+1), self.epd_height, 80 * (row+1)))
        
        # ETA
        self.logger.debug("Drawing ETA(s)")
        for row, entry in enumerate(self.conf):
            co = entry['eta_co']
            del entry['eta_co']
            
            if  self.row_size <= row: 
                self.logger.warning(f"Number of ETA entry in eta.conf ({len(self.conf)}) is larger than allowed display number.  Stoped at {row}.")
                break
            self.logger.debug(f"----- Row {row} -----")
            self.logger.debug(f"Reading entry {str(entry)}")
            
            _dets = dets._Details.get_obj(co)(**entry)
            _eta = eta.Eta.get_obj(co)(**entry)
            
            rte = _dets.get_route_name()
            dest = self._dotted(_dets.get_dest(), 9)
            stop = self._dotted(_dets.get_stop_name(), 9)
            
            # titles
            self.logger.debug(f"Drawing route information")
            self.drawing.text((5, (self.row_h*row + -7)), text=rte, fill=self.black, font=self.f_route)
            self.drawing.text((5, (self.row_h*row + 35)), dest, fill=self.black, font=self.f_text)
            self.drawing.text((5, (self.row_h*row + 55)), f"@{stop}", fill=self.black, font=self.f_text)
            
            # time
            self.logger.debug(f"Drawing ETA information")
            if _eta.error:
                self.logger.info(f"No ETA received: {_eta.msg}")
                self.drawing.text((170, self.row_h*row + 25), text=_eta.msg, fill=self.black, font=self.f_text)
            else:
                for idx, time in enumerate(_eta.get_etas()):
                    if (idx < self.num_etas):
                        self.logger.debug(time)
                        eta_mins = str(time['eta_mins'])
                        if len(eta_mins) <= 3 :
                            self.drawing.text((self.lyo['etax'], self.lyo['etay'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=eta_mins, fill=self.black, font=self.f_mins)
                            self.drawing.text((self.lyo['minx'], self.lyo['miny'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=self.lyo['min_desc'], fill=self.black, font=self.f_min)
                            self.drawing.text((self.lyo['timex'], self.lyo['timey'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=time['eta_time'], fill=self.black, font=self.f_time)
                        else:
                            self.drawing.text((self.lyo['lminx'], self.lyo['lminy'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=eta_mins, fill=self.black, font=self.f_lmins)
                    else: break
        

    def partial_update(self, deg: int, intv: int, times: int, mode: str, img_path: str):
        if mode == "loop":
            # loop mode
            self.logger.debug("Partial update - loop mode")
        if mode == "normal":
            self.logger.debug("Partial update - normal mode")

    def full_update(self, deg: int):
        super().full_update(deg)
    
    def exit(self):
        pass
        
CLS = Epd3in7