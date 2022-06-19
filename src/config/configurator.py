import os
import sys
import importlib
import shutil
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) # src path
from src.config import config
from src.config.routeselector import *
from src.config.epdselector import *
from src.eta import eta
from src.eta import details as dets

ROOT = os.getcwd()

class Configurator:
    
    lang_list = {'1': ("tc", "繁體中文"), '2': ("en", "English")}

    def __init__(self, root: str) -> None:
        self.intput_count = 0
        self.eta_row_size = 0
        # paths
        self.path_eta = os.path.join(root, "conf", "eta.json")
        self.path_epd = os.path.join(root, "conf", "epd.json")
        self.path_epd_list = os.path.join(root, "src", "display", "epd_list.json")        
        
        dir_data = os.path.join(root, "data", "route_data")
        self.eta_co_list: dict[str, Selector] = {
            '1': KmbSelector(dir_data, "tc"),
            # '2':"新巴/城巴",
            # '3':"港鐵-重鐵",
            '4': MtrLrtSelector(dir_data, "tc"),
            '5': MtrBusSelector(dir_data, "tc"),
        }
        self.list_function()

    def __load_confs(self):
        try:
            self.epd_conf = config.get(self.path_epd)
        except FileNotFoundError:
            self.epd_conf = {}
        try:
            self.eta_conf = config.get(self.path_eta)
        except FileNotFoundError:
            self.eta_conf = []
    
    def __select_co(self):
        for idx, co in self.eta_co_list.items():
            print(f"[{idx}] {co.name_tc}")
        _input = input(">> 請選擇: ")
        
        if _input in ('q', 'Q'):
            raise KeyboardInterrupt
        while(_input not in self.eta_co_list.keys()):
            _input = input(">> 輸入無效，請重新選擇: ")
        return self.eta_co_list[_input].select()

    def __select_epd(self):
        epdconf = Epdselector.select_epd(self.path_epd_list)
        self.epd_conf['brand'] =  epdconf[0]
        self.epd_conf['model'] =  epdconf[1]
        epdsize = Epdselector.select_display_size()
        self.epd_conf['size'] =  epdsize
    
    def list_function(self):
        func_list = {
            '1': {'descr':"重新設定/新增設定", 'func': self.new},
            '2': {'descr':"查看現有設定", 'func': self.view},
            '3': {'descr':"修改現有設定", 'func': self.edit},
            '4': {'descr':"刪除設定", 'func': self.remove},
            '5': {'descr':"離開", 'func': exit}
        }
        print("動作：")
        for id, item in func_list.items():
            print(f"[{id}] {item['descr']}")
        
        _input = input("選擇動作：")
        while  _input not in func_list.keys():
            _input = input("選擇不正確，請重新輸入：")
            
        func_list[_input]['func']()
    
    def new(self):        
        # backup old config
        if os.path.exists(self.path_epd):
            shutil.copyfile(self.path_epd, self.path_epd.replace(".json", ".json.bak"))
            os.remove(self.path_epd)
        if os.path.exists(self.path_eta):
            shutil.copyfile(self.path_eta, self.path_eta.replace(".json", ".json.bak"))
            os.remove(self.path_eta)
            
        try:
            self.epd_conf = {}
            self.eta_conf = []
            # epd config 
            self.__select_epd()
            # eta co [loop]
            module = importlib.import_module(f"src.display.{self.epd_conf['brand']}.{self.epd_conf['model'] }")
            max_row = getattr(module, "MAXROW")
            print(f"**所選擇的型號最多能顯示{max_row}個預報。\n**輸入完成按 ctrl+c 或選擇{max_row}個預報後，置設程序將自動結束。")
            for i in range(1, max_row + 1):
                try:
                    print(f"正在輸入：{i}/{max_row}")
                    _rt = self.__select_co()
                    self.eta_conf.append(_rt)
                except KeyboardInterrupt: # user quit
                    break
            # write config
            config.put(self.path_epd , self.epd_conf)
            config.put(self.path_eta , self.eta_conf)
            self.view(refresh=False)
        except (Exception, KeyboardInterrupt) as e:
            print(e)
            # restore backups
            shutil.copyfile(self.path_epd.replace(".json", ".json.bak"), self.path_epd)
            shutil.copyfile(self.path_eta.replace(".json", ".json.bak"), self.path_eta)
        finally:
            if os.path.exists(self.path_epd.replace(".json", ".json.bak")) and os.path.exists(self.path_epd):
                os.remove(self.path_epd.replace(".json", ".json.bak"))
            if os.path.exists(self.path_eta.replace(".json", ".json.bak")) and os.path.exists(self.path_eta):
                os.remove(self.path_eta.replace(".json", ".json.bak"))

    def __veiw_epd(self):
        for descr, content in self.epd_conf.items():
            print(f"[{descr}]\t{content}")
            
    def __view_eta(self):
        for idx, entry in enumerate(self.eta_conf):
            if entry['eta_co'] == eta.Kmb.abbr:
                _dets = dets.DetailsKmb
            elif entry['eta_co'] == "ctb/nwb":  # TODO: ctb/nwb
                pass
            elif entry['eta_co'] == eta.MtrTrain.abbr:  # TODO: mtr_hrt
                _dets = dets.DetailsMtrTrain
            elif entry['eta_co'] == eta.MtrLrt.abbr:
                _dets = dets.DetailsMtrLrt
            elif entry['eta_co'] == eta.MtrBus.abbr:
                _dets = dets.DetailsMtrBus
                
            del entry['eta_co']
            _dets = _dets(**entry)
            orig = _dets.get_orig()
            dest = _dets.get_dest()
            stop = _dets.get_stop_name()
            print(f"[{idx}] {entry['route']:<5}@ {stop}\t\t\t {orig} → {dest}")
    
    def view(self, refresh: bool = True):

        if refresh:
            self.__load_confs()
        # epd conf
        print("----- 墨水屏設定 -----")
        self.__veiw_epd()
        # eta conf
        print("-----預報設定 -----")
        self.__view_eta()
        
    def edit(self):
        self.__load_confs()
        
        print("[0] 墨水屏設定\n[1] 預報設定")
        input_mod = input("請選擇修改項目：")
        while input_mod not in ("0", "1"):
            input_mod = input("輸入無效，請重新選擇: ")
        
        if input_mod == "0": # epd
            print("----- 現有設定 -----")
            self.__veiw_epd()
            print("-----")
            self.__select_epd()
            config.put(self.path_epd , self.epd_conf)
        elif input_mod == "1": # eta
            print("----- 現有設定 -----")
            self.__view_eta()
            print("-----")
            print("[0] 修改\n[1] 刪除")
            input_act = input("請選動作: ")
            while input_act not in ("0", "1"):
                input_act = input("輸入無效，請重新選擇: ")
                
            self.view()
            idx = input("請選擇修改項目: ")
            while idx not in [str(i) for i in range(len(self.eta_conf))]:
                idx = input("輸入無效，請重新選擇: ")
                
            if input_act == "0": # modify
                self.eta_conf[int(idx)] =  self.__select_co()
            elif input_act == "1": # delete
                self.eta_conf.pop(int(idx))

            config.put(self.path_eta , self.eta_conf)
            print("已完成修改:\n")
            self.view(refresh=False)
        
        self.list_function()

    def remove(self):
        confirm = input("確定刪除? [y/n]")
        if confirm.lower() == "y":
            open(self.path_epd, 'w').close()
            open(self.path_eta, 'w').close()
            print("已刪除。")
        else:
            print("已取消。")


if __name__ == "__main__":
    c = Configurator("/home/vm/vscode/RaspberryPi-ETA-Station/")
    c.new()
