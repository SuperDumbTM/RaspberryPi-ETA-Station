import os
import string
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) # lib path
from eta import details as dets
from eta import eta
import epd3in7

PARTIAL = True
MAXROW = 6

class Epd3in7TimeOnly(epd3in7.Epd3in7):
    
    mode = 0
    epd_height: int
    epd_width: int
    black: int
    white: int

    def __init__(self, root: str,size: int) -> None:
        '''
        mode:
            - 0->4Gary mode
            - 1->1Gary mode
        '''
        self.row_h = 80
        self.row_size = 6       
        self.mode = 1
        super().__init__(root, size)
        
    @staticmethod
    def can_partial():
        return PARTIAL    
    
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
            co = entry['eta_co']
            del entry['eta_co']
            
            if  self.row_size <= row: 
                self.logger.warning(f"Number of ETA entry in eta.conf ({len(self.conf)}) is larger than allowed display number.  Stoped at {row}.")
                break
            
            self.logger.debug(f"- Reading entry {entry}")
            _dets = dets._Details.get_obj(co)(**entry)
            _eta = eta.Eta.get_obj(co)(**entry)
            
            rte = _dets.get_route_name()
            dest = self._dotted(_dets.get_dest(), 9)
            stop = self._dotted(_dets.get_stop_name(), 9)
                
            stop = _dets.get_stop_name()
            
            # titles
            self.logger.debug(f"- Drawing row {row}'s route information")
            self.drawing.text((5, (self.row_h*row + -5)), text=rte, fill=self.black, font=self.f_route)
            self.drawing.text((5, (self.row_h*row + 35)), dest, fill=self.black, font=self.f_text)
            self.drawing.text((5, (self.row_h*row + 55)), f"@{stop}", fill=self.black, font=self.f_text)
            
            # time
            self.logger.debug(f"- Drawing row {row}'s ETA time")
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
                            self.drawing.text((self.lyo['lminx'], self.lyo['lminy'] + (self.row_h*row + self.lyo['eta_pad']*idx)), text=eta_mins, fill=self.black, font=self.f_lmins)
                    else: break


CLS = Epd3in7TimeOnly