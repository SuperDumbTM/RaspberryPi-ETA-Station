import json
import datetime
import os
import sys
from abc import ABC, abstractmethod
from typing import Literal
sys.path.append(os.path.join(os.path.dirname((os.path.dirname(os.path.dirname(__file__)))))) # root path
import _request as rqst

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
PATH_DATA = os.path.join("data", "route_data")

class Details(ABC):
    
    @staticmethod
    @abstractmethod
    def get_obj(co: str) -> object:
        """get class by company abbreviation

        Args:
            co (str): abbreviation
        """
    
    @staticmethod
    @abstractmethod
    def update() -> None:
        """
        update the routes file of the class (ETA company)
        """
    
    @staticmethod
    @abstractmethod
    def is_outdated(fpath: str, threshold = 30) -> bool:
        """
        check if the file needs update: 
        - outdated
        - not exists
        """
    
    @abstractmethod
    def get_route_name(self) -> str: pass
    
    @abstractmethod
    def get_stop_name(self) -> str: pass
    
    @abstractmethod
    def _get_ends(self) -> str: pass
    
    @abstractmethod
    def get_dest(self): pass
    
    @abstractmethod
    def get_orig(self): pass

class _Details(Details):
    """NOT intended to be instantiated"""

    today = datetime.date.today().strftime('%Y%m%d')
        
    @staticmethod
    def get_obj(co: str):
        if co == DetailsKmb.abbr:        return DetailsKmb
        elif co == DetailsMtrLrt.abbr:   return DetailsMtrLrt
        elif co == DetailsMtrBus.abbr:   return DetailsMtrBus
        elif co == DetailsMtrTrain.abbr: return DetailsMtrTrain
    
    @staticmethod
    def update_all():
        for scls in _Details.__subclasses__():
            fpath = os.path.join(ROOT, scls.rtepath)
            if _Details.is_outdated(fpath):
                scls.update()
    
    @staticmethod
    def is_outdated(fpath: str, threshold = 30) -> bool:
        today = _Details.today
        try:
            with open(fpath, "r", encoding = "utf-8") as f:
                lastupd = json.load(f)["lastupdate"]
                day_diff = (datetime.datetime.strptime(today, "%Y%m%d") - datetime.datetime.strptime(lastupd, "%Y%m%d")).days
                return True if day_diff > threshold else False
        except FileNotFoundError:
            return True
    
    def __init__(self, route: str, direction: str, service_type: int | None, stop: int | str, lang: str, root: Literal) -> None:
        self.route = str(route).upper()
        self.direction = direction.lower()
        self.service_type = str(service_type)
        self.stop = stop
        self.lang = lang
        if root is not None: 
            self.root = root
        else:
            self.root = ROOT
    
    def get_route_name(self) -> str:
        return self.route

class DetailsKmb(_Details):
    
    abbr = "kmb"
    basedir = os.path.join(PATH_DATA, "kmb")
    rtepath = os.path.join(basedir, "route.json")
    
    def __init__(self, route: str, direction: str, service_type: int | None, stop: int | str, lang: str, root: Literal = None) -> None:
        super().__init__(route, direction, service_type, int(stop), lang, root)
        
        self.rte_path = os.path.join(self.root, self.rtepath)
        fname = f"{self.route}-{self.direction}-{self.service_type}.json"
        self.cache_path = os.path.join(self.root, self.basedir, "cache", fname)

    @staticmethod
    def update():
        dir_trans = {'O': "outbound", 'I': "inbound"}
        data = rqst.kmb_route_detail()['data']
        output = {'lastupdate': _Details.today, 'data': {}}
        od = output['data']

        for entry in data:
            od.setdefault(entry['route'],{})
            od[entry['route']].setdefault(dir_trans[entry['bound']],{})
            entry = od[entry['route']][dir_trans[entry['bound']]].setdefault(entry['service_type'], {
                'orig_en': entry['orig_en'],
                'orig_tc': entry['orig_tc'],
                'orig_sc': entry['orig_sc'],
                'dest_en': entry['dest_en'],
                'dest_tc': entry['dest_tc'],
                'dest_sc': entry['dest_sc'],
            })
            
        with open(os.path.join(ROOT, DetailsKmb.rtepath), "w", encoding="utf-8") as f:
            f.write(json.dumps(output))
    
    def cache(self):
        data = rqst.kmb_route_stop_detail(self.route, self.direction, self.service_type)['data']
        output = {}
        output["lastupdate"] = self.today
        output['data'] = [None] * len(data)

        for stop in data:
            stop_details = rqst.kmb_stop_detail(stop['stop'])['data']
            output['data'][int(stop['seq']) - 1] = {
                'name_en': stop_details['name_en'],
                'name_tc': stop_details['name_tc'],
                'name_sc': stop_details["name_sc"],
                'seq': stop['seq']
            }
            
        with open(self.cache_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(output))

    def get_stop_name(self):
        #NOTE: stop ID -1 due to cache file zero-indexing
        try:
            key = "name_" + self.lang
            if super().is_outdated(self.cache_path):
                self.cache()
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)["data"]
                return data[self.stop - 1][key]
        except Exception as e:
            return "err"
    
    def _get_ends(self, key: str):
        try:
            with open(self.rte_path, "r", encoding="utf-8") as f:
                data = json.load(f)['data']
                return data[self.route][self.direction][self.service_type][key]
        except Exception as e:
            print(e)
            return "err"
    
    def get_dest(self):
        return self._get_ends("dest_" + self.lang)
    
    def get_orig(self):
        return self._get_ends("orig_" + self.lang)

class DetailsMtrLrt(_Details):
    
    abbr = "mtr_lrt"
    basedir = os.path.join(PATH_DATA, "mtr", "lrt")
    rtepath = os.path.join(basedir, "route.json")
    
    def __init__(self, route: str, direction: str, service_type: int | None, stop: int | str, lang: str, root: Literal = None) -> None:
        super().__init__(route, direction, service_type, stop, lang, root)
        self.rte_path = os.path.join(self.root, self.rtepath)
        
    @staticmethod
    def update():
        data = rqst.mtr_lrt_route_stop_detail()
        dir_trans = {'1': "outbound", '2': "inbound"}
        output = {'lastupdate': _Details.today, 'data': {}}
        od = output['data']
        
        # [0]route, [1]direction , [2]stopCode, [3]stopID, [4]stopTCName, [5]stopENName, [6]seq
        for idx in range(1, len(data)):
            line = data[idx].split(",")
            for idx in range(len(line) - 1):
                line[idx] = line[idx].strip("\"")
            line[6] = line[6].split(".")[0].strip("\"")
            
            direct = dir_trans[line[1]]
            route = str(line[3])
            # stop
            od.setdefault(line[0], {'details': {}})
            od[line[0]].setdefault(direct, {})
            od[line[0]][direct][route] = {
                'name_ch': line[4],
                'name_en': line[5],
                'seq': line[6]
            }
            # details
            od[line[0]]['details'].setdefault(direct, {})
            if line[6] in ("1", 1):
                od[line[0]]['details'][direct]['orig'] = {
                    'name_ch': line[4],
                    'name_en': line[5],
                    'stop': route
                }
            else:
                od[line[0]]['details'][direct]['dest'] = {
                    'name_ch': line[4],
                    'name_en': line[5],
                    'stop': route
                }
        
        # 705, 706 modification
        output['data']['705']['details']['outbound']['dest']['name_ch'] = '天水圍循環綫'
        output['data']['705']['details']['outbound']['dest']['name_en'] = 'TSW Circular'
        output['data']['705']['details']['outbound']['dest']['stop'] = '430'
        output['data']['705']['details'].pop('inbound')
        
        output['data']['706']['details']['outbound']['dest']['name_ch'] = '天水圍循環綫'
        output['data']['706']['details']['outbound']['dest']['name_en'] = 'TSW Circular'
        output['data']['705']['details']['outbound']['dest']['stop'] = '430'
        output['data']['706']['details'].pop('inbound')
        
        ib = output['data']['705'].pop('inbound')
        for seq, stop in enumerate(ib.items(), 6):
            stop[1]['seq'] = str(seq)
            output['data']['705']['outbound'].setdefault(stop[0], stop[1])
        ib = output['data']['706'].pop('inbound')
        for seq, stop in enumerate(ib.items(), 13):
            stop[1]['seq'] = str(seq)
            output['data']['706']['outbound'].setdefault(stop[0], stop[1])
        
        with open(os.path.join(ROOT, DetailsMtrLrt.rtepath), 'w', encoding="utf-8") as f:
            f.write(json.dumps(output))
    
    def get_stop_name(self) -> str:
        try:                  
            with open(self.rte_path, 'r', encoding="utf-8") as f:
                data = json.load(f)['data']
                return data[self.route][self.direction][self.stop]["name_" + self.lang]
        except Exception as e:
            return "err"
    
    def _get_ends(self, key):
        try:                
            with open(self.rte_path, "r", encoding="utf-8") as f:
                data = json.load(f)['data']
                return data[self.route]['details'][self.direction][key]["name_" + self.lang]
        except Exception as e:
            return "err"
        
    def get_orig(self):
        return self._get_ends("orig")
    
    def get_dest(self):
        # NOTE: in/outbound of circular routes are NOT its destination
        # NOTE: 705, 706 return "天水圍循環綫"/'TSW Circular' instead of its destination
        if self.route in ("705", "706"):
            return "天水圍循環綫" if self.lang == "ch" else "TSW Circular"
        return self._get_ends("dest")
       
class DetailsMtrBus(_Details):
    
    abbr = "mtr_bus"
    basedir = os.path.join(PATH_DATA, "mtr", "bus")
    rtepath = os.path.join(basedir, "route.json")
    
    def __init__(self, route: str, direction: str, service_type: int | None, stop: int | str, lang: str, root: Literal = None) -> None:
        super().__init__(route, direction, service_type, stop, lang, root)
        self.rte_path = os.path.join(self.root, self.rtepath)
    
    @staticmethod
    def update():
        stop_data = rqst.mtr_bus_stop_detail()
        dir_trans = {"I":"inbound","O":"outbound"}
        output = {'lastupdate': _Details.today, 'data': {}}
        od = output['data']

        # [0]route, [1]direction, [2]seq, [3]stopID, [4]stopLAT, [5]stopLONG, [6]stopTCName, [7]stopENName
        for line in stop_data[1:]:
            line = line.split(",")
            direct = dir_trans[line[1]]
            
            # stop
            od.setdefault(line[0],{'details': {}}) # route no
            od[line[0]].setdefault(direct,{})
            od[line[0]][direct][line[3]] = {
                'seq': line[2],
                'lat': line[4],
                'long': line[5],
                'name_zh': line[6],
                'name_en': line[7]
                }

            # details
            od[line[0]]['details'].setdefault(direct, {})
                # origin
            if line[2] in ("1", 1):
                od[line[0]]['details'][direct]['orig'] = {
                    'name_zh': line[6],
                    'name_en': line[7],
                    'stop_id': line[3]
                }
                # destination
            else:
                od[line[0]]['details'][direct]['dest'] = {
                    'name_zh': line[6],
                    'name_en': line[7],
                    'stop_id': line[3]
                }

        with open(os.path.join(ROOT, DetailsMtrBus.rtepath), "w", encoding="utf-8") as f:
            f.write(json.dumps(output))
    
    def get_stop_name(self) -> str:
        try:                
            with open(self.rte_path, 'r', encoding="utf-8") as f:
                data = json.load(f)['data']
                return data[self.route][self.direction][self.stop]["name_" + self.lang]
        except Exception as e:
            return "err"
    
    def _get_ends(self, key):
        try:
            if self.is_outdated(self.rte_path):
                self.update()
                
            with open(self.rte_path, "r", encoding="utf-8") as f:
                data = json.load(f)['data']
                return data[self.route]['details'][self.direction][key]['name_' + self.lang]
        except Exception as e:
            return "err"

    def get_dest(self):
        return self._get_ends("orig")
    
    def get_orig(self):
        return self._get_ends("dest")
    
    def get_stop_type(self):
        """
        ETAs entry from MTR bus API return data consist of both arrival time and departure time.  
        This function helps to determent which time should use
        
        - original stop             -> departure time
        - mid-way, destination stop -> arrival time
        """
        try:
            if self.is_outdated(self.rte_path):
                self.update()
                
            with open(self.rte_path, "r", encoding="utf-8") as f:
                data = json.load(f)['data']
                if data[self.route]["details"][self.direction]["orig"]["stop_id"] == self.stop:
                    return "orig"
                elif data[self.route]["details"][self.direction]['dest']["stop_id"] == self.stop:
                    return 'dest'
                else:
                    return "mid"
        except Exception as e:
            return "err"
        
class DetailsMtrTrain(_Details):
    
    abbr = "mtr_train"
    basedir = os.path.join(PATH_DATA, "mtr", "train")
    rtepath = os.path.join(basedir, "route.json")    
    route_names = {
        'AEL': {'tc': "機場快線", 'en': "AIR EXP"},
        'TCL': {'tc': "東涌線", 'en': "TCL"},
        'TML': {'tc': "屯馬線", 'en': "TML"},
        'TKL': {'tc': "將軍澳線", 'en': "TKOL"},
        'EAL': {'tc': "東鐵線", 'en': "EAL"}
    }
    
    def __init__(self, route: str, direction: str, service_type: int | None, stop: int | str, lang: str, root: Literal = None) -> None:
        super().__init__(route, direction, service_type, stop, lang, root)
        
        self.rte_path = os.path.join(self.root, self.rtepath)
    
    @staticmethod
    def update():
        data = rqst.mtr_train_route_stop_detail()
        dir_trans = {
            'DT': "inbound",
            'UT': "outbound",
            'LMC-DT': "inbound-LMC",
            'LMC-UT': "outbound-LMC",
            'TKS-DT': "inbound-TKS",
            'TKS-UT': "outbount-TKS"
            }
        output = {'lastupdate': _Details.today, 'data': {}}
        od = output['data']
        
        # line, direction, stopCode, stopID, TCName, ENName, stopSeq
        for row in data[1:]:
            if not row == ",,,,,," : # ignore empty row
                row = row.split(',')
                direct = dir_trans[row[1]]
                
                # stop
                od.setdefault(row[0], {'details': {}})
                od[row[0]].setdefault(direct, {})
                od[row[0]][direct][row[2]] = {
                    'id': row[3],
                    'name_tc': row[4],
                    'name_en': row[5],
                    'seq': row[-1]
                }
                # details
                od[row[0]]['details'].setdefault(direct, {})
                if row[-1] in (1, '1'): # origin
                    od[row[0]]['details'][direct]['orig'] = {
                        'id': row[3],
                        'code': row[2],
                        'name_tc': row[4],
                        'name_en': row[5]
                    }
                else: # destnation
                    od[row[0]]['details'][direct]['dest'] = {
                        'id': row[3],
                        'code': row[2],
                        'name_tc': row[4],
                        'name_en': row[5]
                    }
                    
        with open(os.path.join(ROOT, DetailsMtrTrain.rtepath), "w", encoding="utf-8") as f:
            f.write(json.dumps(output))
    
    def get_route_name(self) -> str:
        return self.route_names[self.route][self.lang]
    
    def get_stop_name(self) -> str:
        try:                
            with open(self.rte_path, 'r', encoding="utf-8") as f:
                data = json.load(f)['data']
                return data[self.route][self.direction][self.stop]["name_" + self.lang]
        except Exception as e:
            return "err"
    
    def _get_ends(self, key):
        try:                
            with open(self.rte_path, "r", encoding="utf-8") as f:
                data = json.load(f)['data']
                return data[self.route]['details'][self.direction][key]['name_' + self.lang]
        except Exception as e:
            return "err"

    def get_dest(self):
        return self._get_ends("orig")
    
    def get_orig(self):
        return self._get_ends("dest")

