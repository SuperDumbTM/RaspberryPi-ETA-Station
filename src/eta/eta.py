import os
import requests
import _request as rqst
import details as dets
import exception as ce
from datetime import datetime, timedelta
from typing import Literal
import logging

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
            self.data = self._get_etas()['data']
            self.eta_len = len(self.data)
            self.error = False
            self.msg = ""
        except ce.APIStatusError:
            self.error = True
            self.msg = "API 錯誤"
            self.eta_len = 0
        except ce.EndOfServices:
            self.error = True
            self.msg = "服務時間已過"
            self.eta_len = 0
        except ce.EmptyDataError:
            self.error = True
            self.msg = "沒有數據"
            self.eta_len = 0
        except requests.exceptions.RequestException as e:
            self.error = True
            self.msg = "網絡錯誤"
            self.eta_len = 0
        except Exception as e:
            self.error = True
            self.msg = "錯誤"
            self.eta_len = 0
        finally:
            pass
    
    @staticmethod
    def get_obj(co: str):
        if co == "kmb":
            return Kmb
        elif co == "mtr_lrt":
            return MtrLrt
        elif co == "mtr_bus":
            return MtrBus

    def get_eta_count(self) -> int:
        return self.eta_len

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

    def __init__(self, eta_co: str, route: str, direction: Literal["inbound", "outbound"], stop: int, service_type: int, lang: Literal["tc", "sc", "en"]):
        '''
        ``dir``: outbound, inbound
        ``lang``: tc, sc, en
        '''
        self.route = route
        self.direction = direction
        self.stop = int(stop)
        self.st = service_type
        self.lang = lang
        
        super().__init__()

    def _get_etas(self) -> dict:
        data = rqst.kmb_eta(self.route.upper(), self.st)['data']
        # E: empty return
        if len(data) == 0: 
            raise ce.APIStatusError

        eta_seq = 1
        output = {}
        output['data'] = []

        #TODO: Optimization: by dir
        #NOTE: the number of ETA entry form API at the same stop may not be 3 every time.  (e.g. N routes provide only 2)
        for stops in data:
            if stops["seq"] == self.stop and stops["dir"]==self.direction[0].upper():
                if stops["eta"] == None:
                    raise ce.EndOfServices

                eta_time = datetime.strptime(stops["eta"], "%Y-%m-%dT%H:%M:%S%z")
                timestamp = datetime.strptime(stops["data_timestamp"], "%Y-%m-%dT%H:%M:%S%z")
                
                output['data'].append(
                    {
                    "co": stops["co"],
                    'eta_mins': (eta_time - timedelta(hours=timestamp.hour, minutes=timestamp.minute)).minute,
                    'eta_time': datetime.strftime(eta_time, "%H:%M"),
                    'remark': stops["rmk_"+self.lang]
                    }
                )
                if eta_seq == 3: break
                eta_seq += 1   
            else:  continue

        # E: empty output
        if output.get('data',1) == 1: 
            raise ce.EmptyDataError
        
        return output

class MtrLrt(Eta):

    def __init__(self, eta_co: str, route: str, direction: None, stop: int, service_type: None, lang: Literal["ch", "en"]):
        '''
        ``lang``: ch, en
        '''
        self.route = route
        self.direction = direction
        self.stop = stop
        self.lang = lang
        self._dets = dets.DetailsMtrLrt(eta_co, route, direction, stop, service_type, lang)
        
        super().__init__()

    def _get_etas(self):
        data = rqst.mtr_lrt_eta(self.stop)
        # E: return status error
        if data["status"] == 0:
            raise ce.APIStatusError

        timestamp = datetime.strptime(data["system_time"], "%Y-%m-%d %H:%M:%S")
        output = {}
        output['data'] = []

        idx = 0
        for platform in data['platform_list']:
            if platform.get("end_service_status",1) != 1:
                raise ce.EndOfServices
            
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
            raise ce.EmptyDataError
        return output

class MtrBus(Eta):

    def __init__(self, eta_co: str, route: str, direction: str, stop: str, service_type: None, lang: Literal["zh", "en"]):
        '''
        ``dir``: outbound, inbound
        ``lang``: zh, en
        '''
        self.route = route
        self.direction = direction
        self.stop = stop
        self.lang = lang
        self._dets = dets.DetailsMtrBus(eta_co, route, direction, service_type, stop, lang)
        
        super().__init__()

    def _get_etas(self):
        data = rqst.mtr_bus_eta(self.route.upper(), self.lang)
        
        if data["status"] == 0: # E: return status error
            raise ce.APIStatusError
        elif data["routeStatusRemarkTitle"]=="停止服務": # E: EOS
            raise ce.EndOfServices
        
        timestamp = datetime.strptime(data["routeStatusTime"], "%Y/%m/%d %H:%M")
        eta_seq = 1
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
                    eta_seq += 1
                break

        # E: empty output
        if output.get('data',1) == 1: 
            raise ce.EmptyDataError
        return output

# debug
if __name__ == "__main__":
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "route_data")
    #cls = Kmb("N269",1,"outbound",1, root,"tc")
    cls = Kmb("co","1","outbound",1,1,"tc")
    #cls = MtrLrt("co" ,"705", "inbound", 540, None, "ch")
    #cls = MtrBus("co", "K76","outbound","K76-U010",None,"zh")
    print("eta\t", cls._get_etas())
    pass