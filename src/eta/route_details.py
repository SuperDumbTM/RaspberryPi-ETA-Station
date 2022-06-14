# This module provide methos to get details of different details of stops/routes
# If any error occurs, return "err" unless otherwise specified 

import json, os
from typing import Literal
import _request as rqst
import details_update as upd

def get_mtr_lrt_stop_name(stop_id: int, fpath: str, lang: Literal["ch", "en"]) -> str:
    try:
        # no update
                
        with open(fpath, 'r', encoding="utf-8") as f:
            data = json.load(f)
            return data['stop'][str(stop_id)]["name_"+lang]
    except Exception as e:
        return "err"

def get_mtr_lrt_orig(route: str, dir: str, fpath: str, lang: Literal["ch", "en"]) -> str:
    try:
        # no update
        
        with open(fpath, "r", encoding="utf-8") as f:
            with open(upd.MTR_LRT_STAT_DATA_DIR,'r',encoding="utf-8") as g:
                route_data = json.load(f)
                stat_data = json.load(g)
                return stat_data['data'][str(route_data[route]["details"][dir]["orig_id"])]["name_"+lang]
    except Exception as e:
        return "err"

def get_mtr_lrt_dest(route: str, dir: str, fpath: str, lang: Literal["ch", "en"]) -> str:
    try:
        # no update
        
        with open(fpath, "r", encoding="utf-8") as f:
            with open(upd.MTR_LRT_STAT_DATA_DIR,'r',encoding="utf-8") as g:
                route_data = json.load(f)
                stat_data = json.load(g)
                return stat_data['stop'][str(route_data[route]["details"][dir]["dest_id"])]["name_"+lang]
    except Exception as e:
        return "err"       

def get_mtr_bus_stop_name(route: str, dir: str, stop_id: str, fpath: str, lang: Literal["zh", "en"]) -> str:
    try:
        if upd.is_outdated(fpath):
            upd.mtr_bus_data_update(fpath)
        
        with open(fpath,"r",encoding="utf-8") as f:
            data = json.load(f)['data']
            return data[route]['stop'][dir][stop_id]["name_"+lang]
    except Exception as e:
        return "err"

def get_mtr_bus_orig(route: str, dir: str, fpath: str, lang: Literal["zh", "en"]) -> str:
    try:
        if upd.is_outdated(fpath):
            upd.mtr_bus_data_update(fpath)
        
        with open(fpath,"r",encoding="utf-8") as f:
            data = json.load(f)['data']
            return data[route]["details"][dir]["orig"]["name_"+lang]
    except Exception as e:
        print(e)
        return "err"

def get_mtr_bus_dest(route: str, dir: Literal["inbound", "outbound"], fpath: str, lang: Literal["zh", "en"]) -> str:
    try:
        if upd.is_outdated(fpath):
            upd.mtr_bus_data_update(fpath)
        
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)['data']
            return data[route]["details"][dir]['dest']["name_"+lang]
    except Exception as e:
        return "err"

def get_mtr_bus_stop_type(route: str, dir: Literal["inbound", "outbound"], stop_id: str, fpath: str) -> str:
    """
    ETAs entry from MTR bus API return data consist of both arrival time and departure time.  
    This function helps to determent which time should use
    
    - original stop             -> departure time
    - mid-way, destination stop -> arrival time
    """
    try:
        with open(fpath,"r",encoding="utf-8") as f:
            data = json.load(f)['data']
            if data[route]["details"][dir]["orig"]["stop_id"] == stop_id:
                return "orig"
            elif data[route]["details"][dir]['dest']["stop_id"] == stop_id:
                return 'dest'
            else:
                return "mid"
    except Exception as e:
        return "err"

def get_kmb_stop_name(route: str, dir: Literal["inbound", "outbound"], stop_seq: int, services_type: int, fpath: str, lang: Literal["tc", "sc", "en"]) -> str:
    try:
        key = "name_"+lang

        if upd.is_outdated(fpath):
            upd.kmb_route_stop_data_update(route, dir, services_type, fpath)

        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)["data"]
            return data[stop_seq][key]
    except Exception as e:
        return "err"
    
def get_kmb_orig(route: str, dir: Literal["inbound", "outbound"], stop_seq: int, services_type: int, fpath: str, lang: Literal["tc", "sc", "en"]) -> str:
    dir_trans = {
        "outbound": "O",
        "inbound": "I"
    }
    
    try:
        key = "orig_" + lang
        
        if upd.is_outdated(fpath):
            upd.kmb_data_update(fpath)
        
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)['data']
            return data[route][dir_trans[dir]][services_type][key]
    except Exception as e:
        return "err"

def get_kmb_dest(route: str, dir: Literal["inbound", "outbound"], stop_seq: int, services_type: int, fpath: str, lang: Literal["tc", "sc", "en"]) -> str:
    dir_trans = {
        "outbound": "O",
        "inbound": "I"
    }
    
    try:
        key = "dest_" + lang
        
        if upd.is_outdated(fpath):
            upd.kmb_data_update(fpath)
        
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)['data']
            return data[route][dir_trans[dir]][services_type][key]
    except Exception as e:
        return "err"
