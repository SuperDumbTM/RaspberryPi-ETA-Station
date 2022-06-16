import shutil
import os
import src.config.routeselector as rtsel
import src.config.epdselector as epdsel
from src.config import _configparser
import src.eta.details as dets

ROOT = os.getcwd()
DP = os.path.join(ROOT, "lib", "display")
ETA_CONF_PATH = os.path.join(ROOT, "conf", "eta.conf")
EPD_CONF_PATH = os.path.join(ROOT, "conf", "epd.conf")
DATA_PATH = os.path.join(ROOT, "data", "route_data")


class Configurator:

    lang_list = {
        '1': ("tc", "繁體中文"),
        '2': ("en", "English")
    }

    def __init__(self, root: str) -> None:
        self.intput_count = 0
        self.eta_row_size = 0
        self.path_eta = os.path.join(root, "conf", "eta.conf")
        self.path_epd = os.path.join(root, "conf", "epd.conf")
        
        dir_data = os.path.join(root, "data")
        self.eta_co_list: dict[str, rtsel.Selector] = {
            '1': rtsel.KmbSelector(dir_data, "tc"),
            # '2':"新巴/城巴",
            # '3':"港鐵-重鐵",
            '4': rtsel.MtrLrtSelector(dir_data, "tc"),
            '5': rtsel.MtrBusSelector(dir_data, "tc")
        }

        self.epd_list_path = os.path.join(root, "display", "epd_list.json")
        self.epd_conf = _configparser.ConfigParser(self.path_epd)
        self.eta_conf = _configparser.ConfigParser(self.path_eta)
        self.list_function()

    def __select_co(self):
        for idx, co in self.eta_co_list.items():
            print(f"[{idx}] {co.get_name()[1]}")
        _input = input(">> 請選擇: ")
        while(_input not in self.eta_co_list.keys()):
            _input = input(">> 輸入無效，請重新選擇: ")
        return self.eta_co_list[_input].select()

    def list_function(self):
        func_list = {
            '1': {'descr':"重新設定/新增設定", 'func': self.new},
            '2': {'descr':"查看現有設定", 'func': self.view},
            '3': {'descr':"修改現有設定", 'func': self.edit},
            '4': {'descr':"刪除設定", 'func': self.remove},
            '5': {'descr':"離開", 'func': exit}
        }
        for id, item in func_list.items():
            print(f"[{id}] {item['descr']}")
        
        _input = input("選擇動作：")
        while  _input not in func_list.keys():
            _input = input("選擇不正確，請重新輸入：")
            
        func_list[_input]['func']()
    
    def new(self):
        # backup old config
        if os.path.exists(self.path_epd):
            shutil.copyfile(
                self.path_epd, self.path_epd.replace(".conf", ".conf.bak"))
            os.remove(self.path_epd)
        if os.path.exists(self.path_eta):
            shutil.copyfile(
                self.path_eta, self.path_eta.replace(".conf", ".conf.bak"))
            os.remove(self.path_eta)

        try:
            self.epd_conf.read()
            self.eta_conf.read()
            # epd config
            self.epd_conf.add_section("epd")
            epdconf = epdsel.Epdselector.select_epd(self.epd_list_path)
            self.epd_conf.add_opt("epd", "brand", epdconf[0])
            self.epd_conf.add_opt("epd", "model", epdconf[1])

            epdsize = epdsel.Epdselector.select_display_size(
                os.path.join(DP, epdconf[0], "size.conf"), epdconf[1])
            self.epd_conf.add_opt("epd", "size", epdsize)
            # eta co
            for i in range(epdsize):
                _rt = self.__select_co()
                self.eta_conf.add_opts(str(i), _rt)
            # write
            self.epd_conf.write()
            self.eta_conf.write()
            c.view()
        except (Exception, KeyboardInterrupt) as e:
            print(e)
            shutil.copyfile(self.path_epd.replace(
                ".conf", ".conf.bak"), self.path_epd)
            shutil.copyfile(self.path_eta.replace(
                ".conf", ".conf.bak"), self.path_eta)
        finally:
            if os.path.exists(self.path_epd.replace(".conf", ".conf.bak")) and os.path.exists(self.path_epd):
                os.remove(self.path_epd.replace(".conf", ".conf.bak"))
            if os.path.exists(self.path_eta.replace(".conf", ".conf.bak")) and os.path.exists(self.path_eta):
                os.remove(self.path_eta.replace(".conf", ".conf.bak"))

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
            elif d['eta_co'] == "ctb/nwb":  # TODO: ctb/nwb
                pass
            elif d['eta_co'] == "mtr_hrt":  # TODO: mtr_hrt
                pass
            elif d['eta_co'] == "mtr_lrt":
                _dets = dets.DetailsMtrLrt(**d)
            elif d['eta_co'] == "mtr_bus":
                _dets = dets.DetailsMtrBus(**d)
            orig = _dets.get_orig()
            dest = _dets.get_dest()
            stop = _dets.get_stop_name()
            print(f"[{idx}] {d['route']:<5}@ {stop}\t\t\t {orig} → {dest}")

    def edit(self):
        if len(self.epd_conf.get_conf()) == 0:
            pass
        else:
            print("[0] 修改\n[1] 刪除")
            input_act = input("請選動作: ")
            while input_act not in ("0", "1"):
                input_act = input("輸入無效，請重新選擇: ")

            self.view()
            input_sec = input("請選擇修改項目: ")
            while input_sec not in self.eta_conf.keys():
                input_sec = input("輸入無效，請重新選擇: ")

            if input_act == "0":
                self.eta_conf.set_section_val(input_sec, self.__select_co())
            elif input_act == "1":
                self.eta_conf.remove_section(input_sec)

            self.epd_conf.write()
            print("已完成修改:\n")
            self.view()

    def remove(self):
        confirm = input("確定刪除? [y/n]")
        if confirm.lower() == "y":
            open(EPD_CONF_PATH, 'w').close()
            print("已刪除。")
        else:
            print("已取消。")


if __name__ == "__main__":
    c = Configurator("/home/vm/vscode/RaspberryPi-ETA-Station/")
    c.new()
