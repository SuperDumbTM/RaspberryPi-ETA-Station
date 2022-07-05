import os
import string
import sys
from PIL import Image,ImageDraw,ImageFont
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) # lib path
# sys.path.append(os.path.dirname(__file__)) # waveshare path
import epd3in7_debug
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

class Epd3in7(epd3in7_debug.Epd3in7):

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
            co = entry['eta_co']
            del entry['eta_co']
                       
            _dets = dets._Details.get_obj(co)(**entry)
            _eta = eta.Eta.get_obj(co)(**entry)
            
            # route
            rte = _dets.get_route_name()
            dest = self._dotted(_dets.get_dest(), 9)
            stop = self._dotted(_dets.get_stop_name(), 9)
                
            stop = _dets.get_stop_name()
            
            # titles
            self.logger.debug(f"- Drawing row {row}'s route information")
            self.drawing.text((5, (self.row_h*row + -5)), text=rte, fill=self.black, font=self.f_route)
            self.drawing.text((5, (self.row_h*row + 35)), dest, fill=self.black, font=self.f_text)
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