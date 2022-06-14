from abc import ABC, abstractmethod
import json
import datetime
import os
from typing import Literal
import _request as rqst

class Details(ABC):
    
    today = datetime.date.today().strftime('%Y%m%d')
    
    @staticmethod
    def get_obj(co: str):
        if co == "kmb":
            return DetailsKmb
        elif co == "mtr_lrt":
            return DetailsMtrLrt
        elif co == "mtr_bus":
            return DetailsMtrBus
    
    def __init__(self, route: str, direction: str, service_type: int | None, stop: int | str, lang: str) -> None:
        self.route = str(route).upper()
        self.direction = direction.lower()
        self.services_type = str(service_type)
        self.stop = stop
        self.lang = lang
    
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
    
class DetailsKmb(Details):
    
    rte_path: str
    cache_path: str
    root = "data/route_data/kmb"
    
    def __init__(self, eta_co: str, route: str, direction: str, service_type: int | None, stop: int | str, lang: str, root: Literal = None) -> None:
        super().__init__(route, direction, service_type, int(stop), lang)
        
        if root is not None: self.root = root
        self.rte_path = os.path.join(self.root, "route.json")
        
        fname = f"{self.route}-{self.direction}-{self.services_type}.json"
        self.cache_path = os.path.join(self.root, "cache", fname)

    def update(self):
        dir_trans = {"O": "outbound", "I": "inbound"}
        data = rqst.kmb_route_detail()['data']
        output = {}
        output["lastupdate"] = self.today
        output['data'] = {}

        for item in data:
            output['data'].setdefault(item["route"],{})
            output['data'][item["route"]].setdefault(dir_trans[item["bound"]],{})

            entry = output['data'][item["route"]][dir_trans[item["bound"]]].setdefault(item["service_type"],{})
            if not output['data'][item["route"]][dir_trans[item["bound"]]].get(item["service_type"],0) == 0:
                entry["orig_en"] = item["orig_en"]
                entry["orig_tc"] = item["orig_tc"]
                entry["orig_sc"] = item["orig_sc"]
                entry["dest_en"] = item["dest_en"]
                entry["dest_tc"] = item["dest_tc"]
                entry["dest_sc"] = item["dest_sc"]

        with open(self.rte_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(output))
            
    def cache(self):
        data = rqst.kmb_route_stop_detail(self.route, self.direction, self.services_type)['data']
        output = {}
        output["lastupdate"] = self.today
        output['data'] = []

        for stop in data:
            stop_detail = rqst.kmb_stop_detail(stop['stop'])['data']
            output['data'].append({
                'name_en': stop_detail['name_en'],
                'name_tc': stop_detail['name_tc'],
                'name_sc': stop_detail["name_sc"],
                'seq': stop['seq']
            })
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
                self.update()
            with open(self.rte_path, "r", encoding="utf-8") as f:
                data = json.load(f)['data']
                return data[self.route][self.direction][self.services_type][key]
        except Exception as e:
            return "err"
    
    def get_dest(self):
        return self._get_ends("dest_" + self.lang)
    
    def get_orig(self):
        return self._get_ends("orig_" + self.lang)

class DetailsMtrLrt(Details):
    
    rte_path: str
    root = "data/route_data/mtr/lrt/"
    
    def __init__(self, eta_co: str, route: str, direction: str, service_type: int | None, stop: int | str, lang: str, root: Literal = None) -> None:
        super().__init__(route, direction, service_type, stop, lang)
        
        if root is not None: self.root = root
        self.rte_path = os.path.join(self.root, "route.json")
        
    def update(self):
        data = rqst.mtr_lrt_route_stop_detail()
        output = {}
        dir_trans = {'1': "outbound", '2': "inbound"}
        output["lastupdate"] = self.today
        output['data'] = {}
        
        prev_dir = dir_trans[data[1].split(",")[1].strip("\"")]
        prev_data = {}
        prev_route = data[1].split(",")[0].strip("\"")
        
        # "Line Code","Direction","Stop Code","Stop ID","Chinese Name","English Name","Sequence"
        for idx in range(1,len(data)):
            line = data[idx].split(",")
            
            route = line[0].strip("\"")
            direction = dir_trans[line[1].strip("\"")]
            stop = line[3].strip("\"")
            name_ch = line[4].strip("\"")
            name_en = line[5].strip("\"")
            stop_seq = line[6].split(".")[0].strip("\"")
            
            
            output['data'].setdefault(route,{'outbound':{}, 'inbound':{}, 'details':{'outbound':{}, 'inbound':{}}})
            # details
            if stop_seq == "1":
                # now orig
                output['data'][route]['details'][direction]['orig'] = {
                    'name_ch': name_ch,
                    'name_en': name_en,
                    'stop': stop
                }
                # previous dest
                output['data'][prev_route]['details'][prev_dir]['dest'] = prev_data
            elif direction != prev_dir:
                # previous dest (same route)(?)
                output['data'][prev_route]['details'][prev_dir]['dest'] = prev_data
            prev_dir = direction
            prev_route = route
            
            prev_data = {
                'name_ch': name_ch,
                'name_en': name_en,
                'stop': stop
            }
            
            # stop data
            output['data'][route][direction][stop] = {
                'name_ch': name_ch,
                'name_en': name_en,
                'seq': stop_seq
            }
        # last entry details
        # previous dest
        output['data'][prev_route]['details'][prev_dir]['dest'] = prev_data
        
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
            
        
        with open(self.rte_path, 'w', encoding="utf-8") as f:
            f.write(json.dumps(output))
    
    def get_stop_name(self) -> str:
        try:
            # no update     
            with open(self.rte_path, 'r', encoding="utf-8") as f:
                data = json.load(f)['data']
                return data[self.route][self.direction][self.stop]["name_" + self.lang]
        except Exception as e:
            return "err"
    
    def _get_ends(self, key):
        try:
        # no update
            with open(self.rte_path, "r", encoding="utf-8") as f:
                data = json.load(f)['data']
                return data[self.route]['details'][self.direction][key]["name_" + self.lang]
        except Exception as e:
            return "err"
        
    def get_orig(self):
        return self._get_ends("orig")
    
    def get_dest(self):
        return self._get_ends("dest")
       
class DetailsMtrBus(Details):
    
    rte_path: str
    root = "data/route_data/mtr/bus/"
    
    def __init__(self, eta_co: str, route: str, direction: str, service_type: int | None, stop: int | str, lang: str, root: Literal = None) -> None:
        super().__init__(route, direction, service_type, stop, lang)
        
        if root is not None: self.root = root
        self.rte_path = os.path.join(self.root, "route.json")
        
    def update(self):
        stop_data = rqst.mtr_bus_stop_detail()
        dir_translation = {"I":"inbound","O":"outbound"}
        output = {}
        output["lastupdate"] = self.today
        output['data'] = {}

        last_rt = "K12" # assume the first route from return is K12 outbound
        last_dir = "O"
        last_details = {}
        for line in stop_data[1:]:
            line = line.split(",")

            output['data'].setdefault(line[0],{}) # route no
            output['data'][line[0]].setdefault('stop',{})

            dir = dir_translation[line[1]]
            output['data'][line[0]]['stop'].setdefault(dir,{}) # direction

            output['data'][line[0]]['stop'][dir][line[3]] = {} # stop id
            output['data'][line[0]]['stop'][dir][line[3]]['seq'] = line[2]
            output['data'][line[0]]['stop'][dir][line[3]]['lat'] = line[4]
            output['data'][line[0]]['stop'][dir][line[3]]['long'] = line[5]
            output['data'][line[0]]['stop'][dir][line[3]]['name_zh'] = line[6]
            output['data'][line[0]]['stop'][dir][line[3]]['name_en'] = line[7]

            # details
            output['data'][line[0]].setdefault('details',{})
            if line[1] == "O": # dir==outbound
                output['data'][line[0]]['details'].setdefault("outbound",{
                    "orig": {
                        'name_zh': "",
                        'name_en': "",
                        'stop_id': ""
                    },
                    "dest": {
                        'name_zh': "",
                        'name_en': "",
                        'stop_id': ""
                    }
                })
                if (int(line[2])==1):
                    output['data'][line[0]]['details'][dir]["orig"]['name_zh'] = line[6]
                    output['data'][line[0]]['details'][dir]["orig"]['name_en'] = line[7]
                    output['data'][line[0]]['details'][dir]["orig"]['stop_id'] = line[3]
            elif line[1] == "I": # dir==inbound
                output['data'][line[0]]['details'].setdefault("inbound",{
                    "orig": {
                        'name_zh': "",
                        'name_en': "",
                        'stop_id': ""
                    },
                    "dest": {
                        'name_zh': "",
                        'name_en': "",
                        'stop_id': ""
                    }
                })
                if int(line[2]) == 1: # seq==1
                    output['data'][line[0]]['details'][dir]["orig"]['name_zh'] = line[6]
                    output['data'][line[0]]['details'][dir]["orig"]['name_en'] = line[7]
                    output['data'][line[0]]['details'][dir]["orig"]['stop_id'] = line[3]

            if line[0]!=last_rt or (line[0] == last_rt and line[1] != last_dir): # start processing next route/dir
                output['data'][last_rt]['details'][last_dir]["dest"] = last_details

            last_rt = line[0]
            last_dir = dir_translation[line[1]]
            last_details = {
                'name_zh': line[6],
                'name_en': line[7],
                'stop_id': line[3]
            }
        output['data'][last_rt]['details'][last_dir]["dest"] = last_details # special case: last route of the return

        with open(self.rte_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(output))
    
    def get_stop_name(self) -> str:
        try:
            if self.is_outdated(self.rte_path):
                self.update()
                
            with open(self.rte_path, 'r', encoding="utf-8") as f:
                data = json.load(f)['data']
                return data[self.route]['stop'][self.direction][self.stop]["name_" + self.lang]
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