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
    
    @staticmethod
    def get_obj(co: str):
        """get class by ETA company abbreviation

        Args:
            co (str): comapany abbreviation
        """
        if co == dets.DetailsKmb.abbr:          return Kmb
        elif co == dets.DetailsMtrLrt.abbr:     return MtrLrt
        elif co == dets.DetailsMtrBus.abbr:     return MtrBus
        elif co == dets.DetailsMtrTrain.abbr:   return MtrTrain
    
    def __init__(self) -> None:
        try:
            self.eta_len = 0
            self.error = True
            self.data = self._fetch_etas()['data']
        except APIError:
            self.msg = "API 錯誤"
        except EndOfService as e:
            self.msg = str(e)
        except EmptyDataError:
            self.msg = "沒有數據"
        except StationClosed:
            self.msg = "車站關閉"
        except AbnormalService:
            self.msg = "正在實施\n特別車務安排"
        except requests.exceptions.RequestException as e:
            self.msg = "網絡錯誤"
        except Exception as e:
            Logger.debug(f"[Unhandled Exception] {e}")
            self.msg = "錯誤"
        else:
            self.msg = ""
            self.error = False
            self.eta_len = len(self.data)
        finally:
            pass   

    def get_eta_count(self) -> int:
        return self.eta_len

    def _fetch_etas(self) -> dict:
        """fetch ETA data from API

        Returns:
            dict: `{'co', 'eta_mins', 'eta_time', 'remark'}`
        """
        pass
    
    def get_etas(self) -> list:
        """get all ETA data returned from API

        Returns:
            list: list of dictionary `{'co', 'eta_mins', 'eta_time', 'remark'}`
        """
        try:
            return self.data
        except AttributeError:
            return []
    
class Kmb(Eta):
    
    def __init__(self, route: str, direction: Literal["inbound", "outbound"], stop: int, service_type: int, lang: Literal["tc", "sc", "en"]):
        self.route = route
        self.direction = direction
        self.stop = int(stop)
        self.st = service_type
        self.lang = lang
        super().__init__()

    def _fetch_etas(self) -> dict:
        data = rqst.kmb_eta(self.route.upper(), self.st)['data']
        
        if len(data) == 0: 
            raise APIError

        eta_seq = 1
        output = {}
        output['data'] = []
        #TODO: Optimization: by dir
        #NOTE: the number of ETA entry form API at the same stop may not be 3 every time.  (e.g. N routes provide only 2)
        for stops in data:
            if stops["seq"] == self.stop and stops["dir"] == self.direction[0].upper():
                if stops["eta"] == None:
                    if stops["rmk_" + self.lang] == "":
                        raise EndOfService("服務時間已過")
                    else:
                        raise EndOfService(stops["rmk_" + self.lang])

                eta_time = datetime.strptime(stops["eta"], "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
                now = datetime.now()
                
                output['data'].append(
                    {
                    "co": stops["co"],
                    'eta_mins': int((eta_time - now).total_seconds() / 60),
                    'eta_time': datetime.strftime(eta_time, "%H:%M"),
                    'remark': stops["rmk_" + self.lang]
                    }
                )
                if eta_seq == 3: break
                eta_seq += 1   
            else:  continue

        if len(output['data']) == 0 : 
            raise EmptyDataError
        
        return output

class MtrLrt(Eta):

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

    def _fetch_etas(self):
        data = rqst.mtr_lrt_eta(self.stop)
        # E: return status error
        if data["status"] == 0:
            raise APIError

        timestamp = datetime.strptime(data["system_time"], "%Y-%m-%d %H:%M:%S")
        output = {}
        output['data'] = []

        for platform in data['platform_list']:
            if platform.get("end_service_status") is not None:
                raise EndOfService("服務時間已過")
            
            for entry in platform['route_list']:
                if entry['route_no'] == self.route and entry[f'dest_{self.lang}'] == self._dets.get_dest():
                    try:
                        eta_min = entry['time_' + self.lang].split(" ")[0]
                        eta_min = int(eta_min)
                    except ValueError:
                        #NOTE: 'eta_mins' may not a be a number due to "即將抵達/離開" -> ValueError
                        output['data'].append({
                                'eta_mins': eta_min,
                                'eta_time': "----",
                                'remark': "",
                        })
                    else:
                        output['data'].append({
                                'eta_mins': eta_min,
                                'eta_time': datetime.strftime(timestamp + timedelta(minutes=int(eta_min)), "%H:%M"),
                                'remark': "",
                        })
                        
        if len(output['data']) == 0 : 
            raise EmptyDataError
        
        return output

class MtrBus(Eta):
    
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

    def _fetch_etas(self):
        data = rqst.mtr_bus_eta(self.route.upper(), self.lang)
        
        # NOTE: Currently, "status" from API always is returned 0
        #   possible due to ETA is in testing stage.
        # -------------------------------------------------------
        # if data["status"] == "0":
        #     raise APIError(data[])
        # elif data["routeStatusRemarkTitle"] == "停止服務":
        #     raise EndOfServices
        if data["routeStatusRemarkTitle"] in ("停止服務", "Non-service hours"):
            raise EndOfService("服務時間已過")
        
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

        if len(output['data']) == 0 : 
            raise EmptyDataError
        
        return output

class MtrTrain(Eta):
    
    dir_trans = {"inbound": "UP", "outbound": "DOWN"}
    dir_rtrans = {'UP': "inbound", 'DOWN': "outbound"}
    
    def __init__(self, route: str, direction: Literal["inbound", "outbound"], stop: int, service_type: int, lang: Literal["tc", "sc", "en"]):
        self.route = route
        self.direction = self.dir_trans[direction]
        self.stop = stop
        self.st = service_type
        self.lang = lang
        super().__init__()

    def _fetch_etas(self) -> dict:
        data: dict = rqst.mtr_train_eta(self.route.upper(), self.stop, self.lang)
        if len(data) == 0: 
            raise APIError
        
        if data['status'] == 0:
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
                    'eta_mins': int((eta_time - timestamp).total_seconds() / 60),
                    'eta_time': datetime.strftime(eta_time, "%H:%M"),
                    'dest': entry['dest'],
                    'remark': data['message']
                    }
                )

            if len(output['data']) == 0 : 
                raise EmptyDataError
            
            return output

# debug
if __name__ == "__main__":
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "route_data")
    # cls = Kmb("N269","outbound",1,1,"tc")
    #cls = Kmb("948","outbound",1,1,"tc")
    #cls = MtrLrt("705", "inbound", 540, None, "ch")
    #cls = MtrBus("K76","outbound","K76-U010",None,"zh")
    #cls = MtrBus("K76","outbound","K76-U010",None,"zh")
    cls = MtrTrain("TKL","inbound","NOP",None,"tc")
    print("eta\t", cls.get_etas())
    print("msg\t", cls.msg)
    pass