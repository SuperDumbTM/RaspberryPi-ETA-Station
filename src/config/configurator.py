import shutil
import os
import routeselector as rtsel
import epdselector as epdsel
import eta.details as dets
import _configparser

ROOT = os.getcwd()
DP = os.path.join(ROOT, "lib", "display")
ETA_CONF_PATH = os.path.join(ROOT, "conf", "eta.conf")
EPD_CONF_PATH = os.path.join(ROOT, "conf", "epd.conf")
DATA_PATH = os.path.join(ROOT, "data", "route_data")

class Configurator:
    
    func_list = {
        "1":"重新設定/新增設定",
        "2":"查看現有設定",
        "3":"修改現有設定",
        "4":"刪除設定",
        "5":"離開"
    }
    eta_co_list: dict[str, rtsel.Selector]  = {
        '1': rtsel.KmbSelector(DATA_PATH, "tc"),
        #'2':"新巴/城巴",
        #'3':"港鐵-重鐵",
        '4': rtsel.MtrLrtSelector(DATA_PATH, "tc"),
        '5': rtsel.MtrBusSelector(DATA_PATH, "tc")
    }
    lang_list={
        '1':("tc","繁體中文"),
        '2':("en","English")
    }  

    def __init__(self) -> None:
        self.intput_count = 0
        self.eta_row_size = 0
        #TODO: (?) input paths from main
        self.epd_list_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "epd_list.json")
        self.epd_conf = _configparser.ConfigParser(EPD_CONF_PATH)
        self.eta_conf = _configparser.ConfigParser(ETA_CONF_PATH)
    
    def __select(self):
        for idx, co in self.eta_co_list.items():
            print(f"[{idx}] {co.get_name()[1]}")
        _input = input(">> 請選擇: ")
        while(_input not in self.eta_co_list.keys()):
            _input = input(">> 輸入無效，請重新選擇: ")
        return self.eta_co_list[_input].select()
    
    def new(self):
        # backup old config
        if os.path.exists(EPD_CONF_PATH): 
            shutil.copyfile(EPD_CONF_PATH, EPD_CONF_PATH.replace(".conf", ".conf.bak"))
            os.remove(EPD_CONF_PATH)
        if os.path.exists(ETA_CONF_PATH): 
            shutil.copyfile(ETA_CONF_PATH, ETA_CONF_PATH.replace(".conf", ".conf.bak"))
            os.remove(ETA_CONF_PATH)
        
        try:
            self.epd_conf.read()
            self.eta_conf.read()
            # epd config
            self.epd_conf.add_section("epd")
            epdconf = epdsel.Epdselector.select_epd(self.epd_list_path)
            self.epd_conf.add_opt("epd", "brand", epdconf[0])
            self.epd_conf.add_opt("epd", "model", epdconf[1])
            
            epdsize = epdsel.Epdselector.select_display_size(os.path.join(DP, epdconf[0], "size.conf"), epdconf[1])
            self.epd_conf.add_opt("epd", "size", epdsize)
            # eta co
            for i in range(epdsize):                   
                _rt = self.__select()
                self.eta_conf.add_opts(str(i), _rt)
            # write
            self.epd_conf.write()
            self.eta_conf.write()
            c.view()
        except (Exception, KeyboardInterrupt) as e:
            print(e)
            shutil.copyfile(EPD_CONF_PATH.replace(".conf", ".conf.bak"), EPD_CONF_PATH)
            shutil.copyfile(ETA_CONF_PATH.replace(".conf", ".conf.bak"), ETA_CONF_PATH)
        finally:
            if os.path.exists(EPD_CONF_PATH.replace(".conf", ".conf.bak")) and os.path.exists(EPD_CONF_PATH):
                os.remove(EPD_CONF_PATH.replace(".conf", ".conf.bak"))
            if os.path.exists(ETA_CONF_PATH.replace(".conf", ".conf.bak")) and os.path.exists(ETA_CONF_PATH):
                os.remove(ETA_CONF_PATH.replace(".conf", ".conf.bak"))
    
    def view(self, refresh: bool = True):
        
        if refresh:
            self.epd_conf.read()
            self.eta_conf.read()
        # epd conf
        opt = self.epd_conf.get_conf()['epd']
        # eta conf
        for idx, d in self.eta_conf.get_conf().items():
            if d['eta_co'] == "kmb":
                _dets = dets.DetailsKmb(**d)
                
            elif d['eta_co'] == "ctb/nwb": #TODO: ctb/nwb
                pass
            elif d['eta_co'] == "mtr_hrt": #TODO: mtr_hrt
                pass
            elif d['eta_co'] == "mtr_lrt":
                _dets = dets.DetailsMtrLrt(**d)
            elif d['eta_co'] == "mtr_bus":
                _dets = dets.DetailsMtrBus(**d)
            orig = _dets.get_orig()
            dest = _dets.get_dest()
            stop = _dets.get_stop_name()
            print(f"{d['route']:<5}@ {stop}\t\t\t {orig} → {dest}")
        
    def edit(self):
        if len(self.epd_conf.get_conf() == 0):
            pass
        else:
            print("[0] 修改\n[1] 刪除")
            input_act = input("請選動作: ")
            while input_act not in ("0","1"):
                input_act = input("輸入無效，請重新選擇: ")

            self.view()
            input_sec = input("請選擇修改項目: ")
            while input_sec not in self.eta_conf.keys():
                input_sec = input("輸入無效，請重新選擇: ")

            if input_act == "0":
                self.eta_conf.set_section_val(input_sec, self.__select())
            elif input_act == "1":
                self.eta_conf.remove_section(input_sec)

            self.epd_conf.write()
            print("已完成修改:\n")
            self.view()
    
    def clear(self):
        open(EPD_CONF_PATH, 'w').close()
    
if __name__ == "__main__":
    c = Configurator()
    c.new()