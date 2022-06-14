# [IMPORTANT]
# Determenting whether the json files should be updated should be implmented in your program.
# The update method of this module DO NOT check whether the data files should be updated or not.
# No update method for MTR LRT because routes' stop platform need manual input

import json
import datetime
import os
from typing import Literal
import _request as rqst

# PAR: parent
# STAT: station
# RT: route
KMB_DATA_DIR = os.path.join(os.path.dirname(__file__),"data/kmb/kmb.json")
KMB_CACHE_PAR_DIR = os.path.join(os.path.dirname(__file__),"data/kmb/route_stop_cache/")
MTR_BUS_DATA_DIR = os.path.join(os.path.dirname(__file__),"data/mtr/bus/route.json")
MTR_LRT_STAT_DATA_DIR = os.path.join(os.path.dirname(__file__),"data/mtr/lrt/station.json")
MTR_LRT_RT_DATA_DIR = os.path.join(os.path.dirname(__file__),"data/mtr/lrt/route.json")
MTR_LRT_RT_DATA_PAR_DIR = os.path.join(os.path.dirname(__file__),"data/mtr/lrt/route/")

_OUTDATED_DAY = 30
_TODAY = datetime.date.today().strftime('%Y%m%d')

def is_outdated(fpath: str) -> bool:
    """
    check if the file needs update: 
    - outdated
    - not exists
    """
    try:
        with open(fpath,"r",encoding="utf-8") as f:
            lastupd = json.load(f)["lastupdate"]
            day_diff = (datetime.datetime.strptime(_TODAY,"%Y%m%d")-datetime.datetime.strptime(lastupd,"%Y%m%d")).days

            return True if day_diff>_OUTDATED_DAY else False
    except FileNotFoundError:
        return True

def kmb_data_update(fpath: str) -> None:
    '''
    update "./data/kmb/kmb.json" is outdated
    '''
    dir_trans = {"O": "outbound", "I": "inbound"}
    
    data = rqst.kmb_route_detail()['data']
    output = {}
    output["lastupdate"] = _TODAY
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

    with open(fpath,"w",encoding="utf-8") as f:
        f.write(json.dumps(output))

def kmb_route_stop_data_update(route: str, dir: Literal["inbound", "outbound"], services_type: int, fpath: str) -> None:
    '''
    update "./data/kmb/route_stop_cache/{route}-{dir}-{services_type}.json"
    '''
    #dest_dir += route+"-"+dir+"-"+str(services_type)+".json"

    route_stop = rqst.kmb_route_stop_detail(route, dir, services_type)['data']
    output = {}
    output["lastupdate"] = _TODAY
    output['data'] = []

    for stop in route_stop:
        stop_detail = rqst.kmb_stop_detail(stop['stop'])['data']
        output['data'].append({
            'name_en': stop_detail['name_en'],
            'name_tc': stop_detail['name_tc'],
            'name_sc': stop_detail["name_sc"],
            'seq': stop['seq']
        })
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(json.dumps(output))

def mtr_bus_data_update(fpath: str) -> None:
    '''
    update if "./data/mtr/bus/route.json" is outdated (lastupdate>``_OUTDATED_DAY`` days)
    '''
    stop_data = rqst.mtr_bus_stop_detail()
    dir_translation = {"I":"inbound","O":"outbound"}
    output = {}
    output["lastupdate"] = _TODAY
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

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(json.dumps(output))
        
def mtr_lrt_data_update(fpath: str):
    data = rqst.mtr_lrt_route_stop_detail()
    output = {}
    dir_trans = {'1': "outbound", '2': "inbound"}
    output["lastupdate"] = _TODAY
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
        
    
    with open(fpath, 'w', encoding="utf-8") as f:
        f.write(json.dumps(output))
        
mtr_lrt_data_update("data/route_data/mtr/lrt/test_route.json")