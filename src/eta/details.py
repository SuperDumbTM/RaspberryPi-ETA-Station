import json
import datetime
import os
import _request as rqst
from abc import ABC, abstractmethod
from src.eta import eta
from typing import Literal

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
PATH_DATA = os.path.join("data", "route_data")
        

class Details(ABC):

    root = ROOT
    today = datetime.date.today().strftime('%Y%m%d')
    
    @staticmethod
    def get_obj(co: str):
        if co == eta.Kmb.abbr:        return DetailsKmb
        elif co == eta.MtrLrt.abbr:   return DetailsMtrLrt
        elif co == eta.MtrBus.abbr:   return DetailsMtrBus
        elif co == eta.MtrTrain.abbr: return DetailsMtrTrain
    
    def __init__(self, route: str, direction: str, service_type: int | None, stop: int | str, lang: str) -> None:
        self.route = str(route).upper()
        self.direction = direction.lower()
        self.service_type = str(service_type)
        self.stop = stop
        self.lang = lang
    
    @staticmethod
    @abstractmethod
    def update(self): pass
    
    def is_outdated(self, fpath: str, outdated = 30) -> bool:
        """
        check if the file needs update: 
        - outdated
        - not exists
        """
        try:
            with open(fpath, "r", encoding = "utf-8") as f:
                lastupd = json.load(f)["lastupdate"]
                day_diff = (datetime.datetime.strptime(self.today, "%Y%m%d") - datetime.datetime.strptime(lastupd, "%Y%m%d")).days
                return True if day_diff > outdated else False
        except FileNotFoundError:
            return True
    
    @abstractmethod
    def get_stop_name(self) -> str: pass
    
    @abstractmethod
    def _get_ends(self) -> str: pass
    
    @abstractmethod
    def get_dest(self): pass
    
    @abstractmethod
    def get_orig(self): pass

class DetailsFactory(ABC):
    
    def get_details() -> Details:
        pass
  
class DetailsKmb(Details):
    
    relpath = os.path.join(PATH_DATA, "kmb")
    
    def __init__(self, route: str, direction: str, service_type: int | None, stop: int | str, lang: str, root: Literal = None) -> None:
        super().__init__(route, direction, service_type, int(stop), lang)
        
        if root is not None: self.root = root
        self.rte_path = os.path.join(self.root, self.relpath, "route.json")
        
        fname = f"{self.route}-{self.direction}-{self.service_type}.json"
        self.cache_path = os.path.join(self.root, self.relpath, "cache", fname)

    @staticmethod
    def update():
        dir_trans = {'O': "outbound", 'I': "inbound"}
        data = rqst.kmb_route_detail()['data']
        output = {'lastupdate': Details.today, 'data': {}}
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
            
        with open(os.path.join(ROOT, DetailsKmb.relpath), "w", encoding="utf-8") as f:
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
            if self.is_outdated(self.cache_path):
                self.cache()
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)["data"]
                return data[self.stop - 1][key]
        except Exception as e:
            return "err"
    
    def _get_ends(self, key: str):
        try:
            if self.is_outdated(self.rte_path):
                DetailsKmb.update()
            with open(self.rte_path, "r", encoding="utf-8") as f:
                data = json.load(f)['data']
                return data[self.route][self.direction][self.service_type][key]
        except Exception as e:
            return "err"
    
    def get_dest(self):
        return self._get_ends("dest_" + self.lang)
    
    def get_orig(self):
        return self._get_ends("orig_" + self.lang)

class DetailsMtrLrt(Details):
    
    relpath = os.path.join(PATH_DATA, "mtr", "lrt", "route.json")
    
    def __init__(self, route: str, direction: str, service_type: int | None, stop: int | str, lang: str, root: Literal = None) -> None:
        super().__init__(route, direction, service_type, stop, lang)
        
        if root is not None: self.root = root
        self.rte_path = os.path.join(self.root, self.relpath)
        
    @staticmethod
    def update():
        data = rqst.mtr_lrt_route_stop_detail()
        dir_trans = {'1': "outbound", '2': "inbound"}
        output = {'lastupdate': Details.today, 'data': {}}
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
        
        with open(os.path.join(ROOT, DetailsMtrLrt.relpath), 'w', encoding="utf-8") as f:
            f.write(json.dumps(output))
    
    def get_stop_name(self) -> str:
        try:
            if self.is_outdated(self.rte_path, 90):
                DetailsMtrLrt.update()   
                  
            with open(self.rte_path, 'r', encoding="utf-8") as f:
                data = json.load(f)['data']
                return data[self.route][self.direction][self.stop]["name_" + self.lang]
        except Exception as e:
            return "err"
    
    def _get_ends(self, key):
        try:
            if self.is_outdated(self.rte_path, 90):
                DetailsMtrLrt.update()
                
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
       
class DetailsMtrBus(Details):
    
    relpath  = os.path.join(PATH_DATA, "mtr", "bus", "route.json")
    
    def __init__(self, route: str, direction: str, service_type: int | None, stop: int | str, lang: str, root: Literal = None) -> None:
        super().__init__(route, direction, service_type, stop, lang)
        
        if root is not None: self.root = root
        self.rte_path = os.path.join(self.root, self.relpath)
    
    @staticmethod
    def update():
        stop_data = rqst.mtr_bus_stop_detail()
        dir_trans = {"I":"inbound","O":"outbound"}
        output = {'lastupdate': Details.today, 'data': {}}
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

        with open(os.path.join(ROOT, DetailsMtrBus.relpath), "w", encoding="utf-8") as f:
            f.write(json.dumps(output))
    
    def get_stop_name(self) -> str:
        try:
            if self.is_outdated(self.rte_path):
                DetailsMtrLrt.update()
                
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
        
class DetailsMtrTrain(Details):
    
    relpath =  os.path.join(PATH_DATA, "mtr", "train", "route.json")
    
    def __init__(self, route: str, direction: str, service_type: int | None, stop: int | str, lang: str, root: Literal = None) -> None:
        super().__init__(route, direction, service_type, stop, lang)
        
        if root is not None: self.root = root
        self.rte_path = os.path.join(self.root, self.relpath)
    
    @staticmethod
    def update():
        data = rqst.mtr_train_route_stop_detail()
        dir_trans = {
            'DT': "inbound",
            'UT': "outbound",
            'LMC-DT': "inbound-LMC",
            'LMC-UT': "outbound-LMC",
            'TKS-DT': "inbound-TKS",
            'TKS-UT': "outbount-TKS"}
        output = {'lastupdate': Details.today, 'data': {}}
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
                    
        with open(os.path.join(ROOT, DetailsMtrTrain.relpath), "w", encoding="utf-8") as f:
            f.write(json.dumps(output))
    
    def get_stop_name(self) -> str:
        try:
            if self.is_outdated(self.rte_path):
                DetailsMtrTrain.update()
                
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

DetailsMtrLrt.update()