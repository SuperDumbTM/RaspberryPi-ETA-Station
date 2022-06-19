import os
import requests
import _request as rqst
import details as dets
import logging
from eta_exceptions import *
from datetime import datetime, timedelta
from typing import Literal

Logger = logging.getLogger(__name__)

class Eta:

    dest: str
    stop: str | int
    eta_len: int
    error: bool
    msg: str
    data: list
    
    def __init__(self) -> None:
        try:
            self.eta_len = 0
            self.error = True
            self.data = self.get_etas_data()['data']
        except APIStatusError:
            self.msg = "API 錯誤"
        except EndOfServices:
            self.msg = "服務時間已過"
        except EmptyDataError:
            self.msg = "沒有數據"
        except StationClosed:
            self.msg = "車站關閉"
        except AbnormalService:
            self.msg = "正在實施\n特別車務安排"
        except requests.exceptions.RequestException:
            self.msg = "網絡錯誤"
        except Exception as e:
            print(e)
            self.msg = "錯誤"
        else:
            self.msg = ""
            self.error = False
            self.eta_len = len(self.data)
        finally:
            pass
    
    @staticmethod
    def get_obj(co: str):
        if co == Kmb.abbr:          return Kmb
        elif co == MtrLrt.abbr:     return MtrLrt
        elif co == MtrBus.abbr:     return MtrBus
        elif co == MtrTrain.abbr:   return MtrTrain

    def get_eta_count(self) -> int:
        return self.eta_len

    def get_etas_data(self) -> dict:
        pass

    def get_eta(self, seq: int = 0) -> tuple:
        '''
        Special cases:
        1. ``seq``: eta sequence no, if ``seq`` less than available eta sequences, return ["",""]
        2. Error occurs: return [message,""]


        @Return:
        ``[0]``: eta in miniutes
        ``[1]``: eta in time
        '''
        if self.error:
            return (self.msg, "--")
        elif seq > self.get_eta_count():
            return ("---", "--")
        else:
            return (self.data[seq]['eta_mins'], self.data[seq]['eta_time'])
    
    def get_etas(self):
        try:
            return self.data
        except AttributeError:
            return []
    
class Kmb(Eta):

    abbr = 'kmb'

    def __init__(self, route: str, direction: Literal["inbound", "outbound"], stop: int, service_type: int, lang: Literal["tc", "sc", "en"]):
        self.route = route
        self.direction = direction
        self.stop = int(stop)
        self.st = service_type
        self.lang = lang
        super().__init__()

    def get_etas_data(self) -> dict:
        data = rqst.kmb_eta(self.route.upper(), self.st)['data']
        # E: empty return
        if len(data) == 0: 
            raise APIStatusError

        eta_seq = 1
        output = {}
        output['data'] = []

        #TODO: Optimization: by dir
        #NOTE: the number of ETA entry form API at the same stop may not be 3 every time.  (e.g. N routes provide only 2)
        for stops in data:
            if stops["seq"] == self.stop and stops["dir"]==self.direction[0].upper():
                if stops["eta"] == None:
                    raise EndOfServices

                eta_time = datetime.strptime(stops["eta"], "%Y-%m-%dT%H:%M:%S%z")
                #timestamp = datetime.strptime(stops["data_timestamp"], "%Y-%m-%dT%H:%M:%S%z")
                now = datetime.now()
                
                output['data'].append(
                    {
                    "co": stops["co"],
                    'eta_mins': (eta_time - timedelta(hours=now.hour, minutes=now.minute)).minute,
                    'eta_time': datetime.strftime(eta_time, "%H:%M"),
                    'remark': stops["rmk_"+self.lang]
                    }
                )
                if eta_seq == 3: break
                eta_seq += 1   
            else:  continue

        # E: empty output
        if output.get('data',1) == 1: 
            raise EmptyDataError
        
        return output

class MtrLrt(Eta):

    abbr = "mtr_lrt"

    def __init__(self, route: str, direction: None, stop: int, service_type: None, lang: Literal["ch", "en"]):
        '''
        ``lang``: ch, en
        '''
        self.route = route
        self.direction = direction
        self.stop = stop
        self.lang = lang
        self._dets = dets.DetailsMtrLrt(route, direction, stop, service_type, lang)
        
        super().__init__()

    def get_etas_data(self):
        data = rqst.mtr_lrt_eta(self.stop)
        # E: return status error
        if data["status"] == 0:
            raise APIStatusError

        timestamp = datetime.strptime(data["system_time"], "%Y-%m-%d %H:%M:%S")
        output = {}
        output['data'] = []

        for platform in data['platform_list']:
            if platform.get("end_service_status",1) != 1:
                raise EndOfServices
            
            for entry in platform['route_list']:
                if entry['route_no'] == self.route and entry[f'dest_{self.lang}'] == self._dets.get_dest():
                    try:
                        eta_min = entry['time_' + self.lang].split(" ")[0]
                        int(eta_min)
                    except ValueError:
                        output['data'].append({
                                'eta_mins': eta_min,
                                #NOTE: 'eta_mins' may not a be a number due to "即將抵達/離開" -> ValueError
                                'eta_time': "----",
                                'remark': "",
                        })
                    else:
                        output['data'].append({
                                'eta_mins': eta_min,
                                #NOTE: 'eta_mins' may not a be a number due to "即將抵達/離開" -> ValueError
                                'eta_time': datetime.strftime(timestamp + timedelta(minutes=int(eta_min)), "%H:%M"),
                                'remark': "",
                        })
                        
        # E: empty output
        if output.get('data') is None: 
            raise EmptyDataError
        return output

class MtrBus(Eta):

    abbr = "mtr_bus"
    
    def __init__(self, route: str, direction: str, stop: str, service_type: None, lang: Literal["zh", "en"]):
        '''
        ``dir``: outbound, inbound
        ``lang``: zh, en
        '''
        self.route = route
        self.direction = direction
        self.stop = stop
        self.lang = lang
        self._dets = dets.DetailsMtrBus(route, direction, service_type, stop, lang)
        
        super().__init__()

    def get_etas_data(self):
        data = rqst.mtr_bus_eta(self.route.upper(), self.lang)
        
        if data["status"] == 0: # E: return status error
            raise APIStatusError
        elif data["routeStatusRemarkTitle"]=="停止服務": # E: EOS
            raise EndOfServices
        
        timestamp = datetime.strptime(data["routeStatusTime"], "%Y/%m/%d %H:%M")
        output = {}
        output['data'] = []
        
        for stops in data["busStop"]:
            if stops["busStopId"] == self.stop:
                for bus in stops["bus"]:
                    entry = {}
                    # eta_mins
                    if self._dets.get_stop_type() == 'orig':
                        time_ref = "departure"
                    elif self._dets.get_stop_type() in ("mid","dest"):
                        time_ref = "arrival"
                    entry['eta_mins'] = bus[time_ref+"TimeText"].split(" ")[0]

                    # eta_time
                    try:
                        entry['eta_time'] = datetime.strftime(timestamp + timedelta(seconds = int(bus[time_ref + "TimeInSecond"])), "%H:%M")
                    except ValueError:
                        entry['eta_time'] = "--"

                    # remark
                    if bus["isScheduled"]:
                        if self.lang == "zh": entry['remark'] = "原定班次"
                        else: entry['remark'] = "Scheduled Bus"
                    else:
                        entry['remark'] = ""

                    output['data'].append(entry)
                break

        # E: empty output
        if output.get('data',1) == 1: 
            raise EmptyDataError
        return output

class MtrTrain(Eta):
    
    abbr = "mtr_train"
    dir_trans = {"inbound": "UP", "outbound": "DOWN"}
    dir_rtrans = {'UP': "inbound", 'DOWN': "outbound"}
    
    def __init__(self, route: str, direction: Literal["inbound", "outbound"], stop: int, service_type: int, lang: Literal["tc", "sc", "en"]):
        self.route = route
        self.direction = self.dir_trans[direction]
        self.stop = stop
        self.st = service_type
        self.lang = lang
        super().__init__()

    def get_etas_data(self) -> dict:
        data: dict = rqst.mtr_train_eta(self.route.upper(), self.stop, self.lang)
        # E: empty return
        if len(data) == 0: 
            raise APIStatusError
        
        if not data['status']:
            if "suspended" in data['message']:
                raise StationClosed
            elif data.get('url') is not None:
                raise AbnormalService
        else:
            timestamp = datetime.strptime(data["sys_time"], "%Y-%m-%d %H:%M:%S")
            e_data = data['data'][f'{self.route}-{self.stop}']
            output = {}
            output['data'] = []

            for entry in e_data[self.direction]:
                eta_time = datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S")
                
                output['data'].append(
                    {
                    'eta_mins': (eta_time - timedelta(hours=timestamp.hour, minutes=timestamp.minute)).minute,
                    'eta_time': datetime.strftime(eta_time, "%H:%M"),
                    'dest': entry['dest'],
                    'remark': data['message']
                    }
                )

            # E: empty output
            if output.get('data', 1) == 1: 
                raise EmptyDataError
            return output

# debug
if __name__ == "__main__":
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "route_data")
    #cls = Kmb("N269",1,"outbound",1, root,"tc")
    #cls = Kmb("948","outbound",1,1,"tc")
    #cls = MtrLrt("705", "inbound", 540, None, "ch")
    #cls = MtrBus("K76","outbound","K76-U010",None,"zh")
    #cls = MtrBus("K76","outbound","K76-U010",None,"zh")
    cls = MtrTrain("TML","outbound","TIS",None,"tc")
    print("eta\t", cls.get_etas())
    pass