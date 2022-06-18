from abc import abstractmethod, ABC
import os
import sys
import json
import datetime
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)))) # scr/
from eta import details as dets

class Selector:
    # returns
    name: tuple
    route: str
    direction: str
    service_type: int
    stop: str
    lang: str
    # hint
    trans_lang: dict
    route_data: dict
    dir_opts: list
    rte_path: os.path
    trans_direction = {'O': "outbound", 'I': "inbound"}
    # var
    trans_lang: dict
    name_tc: str
    
    def __init__(self, data_path: str, lang: str) -> None:
        self.dir_opts = []
        self.root = data_path
        self.lang = self.trans_lang[lang]
    
    def sel_route(self): 
        with open(self.rte_path, "r", encoding="utf-8") as f:
            self.route_data = json.load(f)['data']
            _input = input(">> 請輸入路線編號: ").upper()
            while _input not in self.route_data.keys():
                _input = input(">> 路線不存在，請重新輸入: ").upper()
        self.route = _input
    
    @abstractmethod
    def print_descrp(self):
        self.dir_opts = []
    
    def sel_direction(self):
        choice = ", ".join(self.dir_opts)
        _input = input(f">> 請選行車方向 [{choice}]: ").upper()
        while _input not in self.dir_opts:
            _input = input(">> 行車方向選項不存在，請重新輸入: ").upper()
        self.direction = self.trans_direction[_input]
    
    # @abstractmethod
    # def sel_lang(self): pass
    
    @abstractmethod
    def sel_stop(self): pass
    
    def select(self) -> dict:
        self.sel_route()
        self.print_descrp()
        self.sel_direction()
        self.sel_stop()
        
        return {
            'eta_co': self.name[0],
            'route': self.route,
            'direction': self.direction,
            'service_type': None,
            'stop': self.stop,
            'lang': self.lang
        }

class SelectorWithServiceType(Selector):
    
    st_opts: list
    
    def __init__(self, data_path: str, lang: str) -> None:
        super().__init__(data_path, lang)
    
    @abstractmethod
    def sel_service_type(self): pass
    
    def select(self) -> dict:
        self.sel_route()
        self.print_descrp()
        self.sel_direction()
        self.sel_service_type()
        self.sel_stop()
        
        return {
            'eta_co': self.name[0],
            'route': self.route,
            'direction': self.direction,
            'service_type': self.service_type,
            'stop': self.stop,
            'lang': self.lang
        }
    
    def print_descrp(self):
        self.st_opts = []
        return super().print_descrp()
    
class KmbSelector(SelectorWithServiceType):
    
    name_tc = "九巴"
    trans_lang = {'tc': "tc", 'sc': "sc", 'en': "en"}
    
    def __init__(self, data_path: str, lang: str) -> None:
        super().__init__(data_path, lang)
        self.rte_path = os.path.join(self.root, "kmb", "route.json")
        self.name = ("kmb", "九巴")
      
    def print_descrp(self):
        super().print_descrp()
        descr = {
            'O': "去程 [O]:",
            'I': "回程 [I]:"
        }
        # outbound
        
        for dir in ("O", "I"):
            if self.route_data[self.route].get(self.trans_direction[dir]) is not None:
                self.dir_opts.append(dir)
                print(descr[dir])
                #self.st_opts[dir] = []
                for st in self.route_data[self.route][self.trans_direction[dir]]:
                    self.st_opts.append(st)
                    orig = self.route_data[self.route][self.trans_direction[dir]][st]['orig_' + self.lang]
                    dest = self.route_data[self.route][self.trans_direction[dir]][st]['dest_' + self.lang]
                    print(f"\t[{st}] {orig}→{dest}")
   
    def sel_service_type(self):
        _input = input(">> 請選擇班次類型: ")
        while _input not in self.st_opts:
            _input = input(">> 班次類別不存在，請重新輸入: ")
        self.service_type = int(_input)
        
    def sel_stop(self):
        cache_path = os.path.join(self.root, "kmb", "cache", f"{self.route}-{self.direction}-{self.service_type}.json")
        _upd = dets.DetailsKmb(self.name[0], self.route, self.direction, self.service_type, 0, self.lang)
        
        if _upd.is_outdated(cache_path):
            _upd.cache()
            
        with open(cache_path, 'r', encoding="utf-8") as f:
            stops = json.load(f)["data"]
            print(f"{self.route} {self.direction} {self.service_type} - 車站列表")
            
            # one indexing
            for idx, stop in enumerate(stops, start=1):
                print("{seq:<4} {name}".format(seq="[" + str(idx) + "]", name=stop['name_' + self.lang]))

            
            _input = input(">> 請輸入車站編號: ")
            while _input not in str(tuple(range(0, len(stops)+1))):
                _input = input(">> 輸入無效，請重新選擇: ")
            # while True:
            #     try:
            #         if int(_input) <= 0 or int(_input) > len(stops):
            #             _input = input(">> 輸入無效，請重新選擇: ")
            #         else: 
            #             break
            #     except ValueError:
            #         _input = input(">> 車站選項不存在，請重新輸入: ")
            self.stop = _input
              
class MtrBusSelector(Selector):

    name_tc = "港鐵：巴士"
    trans_lang = {'tc': "zh", 'sc': "zh", 'en': "en"}
    
    def __init__(self, data_path: str, lang: str) -> None:
        super().__init__(data_path, lang)
        self.rte_path = os.path.join(self.root, "mtr", "bus", "route.json")
        self.name = ("mtr_bus", "港鐵巴士")
    
    def print_descrp(self):
        super().print_descrp()
        descr = {
            'O': "去程 [O]:",
            'I': "回程 [I]:"
        }
        
        # if circular, only 'outbound' exists.
        for dir in ("O", "I"):
            if self.route_data[self.route]['details'].get(self.trans_direction[dir]) is not None:
                self.dir_opts.append(dir)
                print(descr[dir])
                orig = self.route_data[self.route]['details'][self.trans_direction[dir]]['orig']['name_' + self.lang]
                dest = self.route_data[self.route]['details'][self.trans_direction[dir]]['dest']['name_' + self.lang]
                print(f"\t {orig}→{dest}")
        
    def sel_stop(self):
        fpath = os.path.join(self.root, "mtr", "bus", "route.json")
        _upd = dets.DetailsMtrBus(self.name[0], self.route, self.direction, None, 0, self.lang)
        if _upd.is_outdated(fpath):
            _upd.update()
            
        with open(fpath, 'r', encoding="utf-8") as f:
            stops = json.load(f)["data"][self.route]['stop'][self.direction]
            print(f"{self.route} {self.direction} - 車站列表")
            
            # zero indexing
            for idx, stop in enumerate(stops.values()):
                print("{seq:<4} {name}".format(seq="[" + str(idx) + "]", name=stop['name_' + self.lang]))

            
            _input = input(">> 請輸入車站編號: ")
            while _input not in str(tuple(range(len(stops)))):
                _input = input(">> 輸入無效，請重新選擇: ")
            # while True:
            #     try:
            #         if int(_input) < 0 or int(_input) > len(stops)-1:
            #             _input = input(">> 輸入無效，請重新選擇: ")
            #         else: 
            #             break
            #     except ValueError:
            #         _input = input(">> 車站選項不存在，請重新輸入: ") 
            self.stop = list(stops.keys())[int(_input)]
        
class MtrLrtSelector(Selector):
    
    name_tc = "港鐵：輕鐵"
    trans_lang = {'tc': "ch", 'sc': "ch", 'en': "en"}
    
    def __init__(self, data_path: str, lang: str) -> None:
        super().__init__(data_path, lang)
        self.rte_path = os.path.join(self.root, "mtr", "lrt", "route.json")
        #self.st_path = os.path.join(self.root, "mtr", "lrt", "station.json")
        self.name = ("mtr_lrt", "港鐵輕鐵")
    
    def print_descrp(self):
        super().print_descrp()
        descr = {
            'O': "去程 [O]:",
            'I': "回程 [I]:"
        }
        
        # if circular, only 'outbound' exists.
        #TODO: standarize json format for lrt
        for dir in ("O", "I"):
            if self.route_data[self.route].get(self.trans_direction[dir]) is not None:
                self.dir_opts.append(dir)
                print(descr[dir])
                orig = self.route_data[self.route]['details'][self.trans_direction[dir]]['orig']['name_' + self.lang]
                dest = self.route_data[self.route]['details'][self.trans_direction[dir]]['dest']['name_' + self.lang]
                print(f"\t {orig}→{dest}")
    
    def sel_direction(self):
        choice = ", ".join(self.dir_opts)
        _input = input(f">> 請選行車方向 [{choice}]: ").upper()
        while _input not in self.dir_opts:
            _input = input(">> 行車方向選項不存在，請重新輸入: ").upper()
        self.direction = self.trans_direction[_input]
        
    def sel_stop(self):
        fpath = os.path.join(self.root, "mtr", "lrt", "route.json")
        with open(fpath, "r", encoding="utf-8") as f:
            stops = json.load(f)['data'][self.route][self.direction]
        
        # zero indexing
        for id, stop in stops.items():
            print("{seq:<4} {name}".format(seq="[" + str(id) + "]", name=stop['name_' + self.lang]))
            
        _input = input(">> 請輸入車站編號: ")
        while _input not in stops.keys():
            _input = input(">> 輸入無效，請重新選擇: ")
        
        self.stop = _input

if __name__ == "__main__":
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "route_data")
    #cls = KmbSelector(root, "tc")
    #cls = MtrBusSelector(root, "tc")
    cls = MtrLrtSelector(root, "tc")
    print(cls.select())