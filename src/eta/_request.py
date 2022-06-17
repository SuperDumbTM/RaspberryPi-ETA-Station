from typing import Literal
import requests, json

# -------------------- eta --------------------

def kmb_eta(route: str, services_type: int) -> dict: 
    '''
    Get KMB ETA data by route from https://data.gov.hk/en-data/dataset/hk-td-tis_21-etakmb/resource/3604afb8-b2c2-4d47-a637-dfab77fc4d72

    Details: https://data.gov.hk/en-data/dataset/hk-td-tis_21-etakmb

    @Exception
    - HTTPError
    '''

    url = "https://data.etabus.gov.hk/v1/transport/kmb/route-eta/{r}/{t}".format(r=route,t=services_type)
    response = requests.get(url)
    response.raise_for_status()
    data = json.loads(response.text)

    return data

def mtr_bus_eta(route: str, lang: Literal["zh", "en"]) -> dict:
    '''
    Get MTR bus eta by route from https://data.gov.hk/en-data/dataset/mtr-mtr_bus-mtr-bus-eta-data/resource/44cba19e-56fe-49b8-b1a0-29b0fb2ef433

    Details: https://data.gov.hk/en-data/dataset/mtr-mtr_bus-mtr-bus-eta-data
    
    @Exception
    - HTTPError
    '''

    data = {"language":lang, "routeName":route}
    url = "https://rt.data.gov.hk/v1/transport/mtr/bus/getSchedule"
    response = requests.post(url, json=data)
    response.raise_for_status()
    data = json.loads(response.text)

    return data
    
def mtr_lrt_eta(stop: int) -> dict:
    '''
    Get MTR LRT eta by station from https://data.gov.hk/en-data/dataset/mtr-lrnt_data-light-rail-nexttrain-data/resource/e9cee6d8-4b12-4a0f-8d09-5924dd2db218

    Details: https://data.gov.hk/en-data/dataset/mtr-lrnt_data-light-rail-nexttrain-data
    
    @Exception
    - HTTPError
    '''

    params = {"station_id": stop}
    headers = {}
    url = "https://rt.data.gov.hk/v1/transport/mtr/lrt/getSchedule"
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    data = json.loads(response.text)

    return data

def mtr_train_eta(route: str, stop: str, lang: Literal["TC", "EN"]) -> dict:
    '''
    Get MTR LRT eta by route and station from https://data.gov.hk/en-data/dataset/mtr-data2-nexttrain-data/resource/744cd43f-4f0d-4f58-b244-78486efc68eb

    Details: https://data.gov.hk/en-data/dataset/mtr-data2-nexttrain-data

    @Exception
    - HTTPErrors
    '''

    params = {"line": route, "sta":stop, "lang": lang}
    url = "https://rt.data.gov.hk/v1/transport/mtr/getSchedule.php"
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = json.loads(response.text)

    return data

# -------------------- details --------------------

def mtr_bus_stop_detail() -> list: 
    '''
    Get MTR bus stops csv from https://data.gov.hk/tc-data/dataset/mtr-data-routes-fares-barrier-free-facilities/resource/dfd4b454-e5e1-4ed8-b15d-99beb82f280c

    Details: https://data.gov.hk/tc-data/dataset/mtr-data-routes-fares-barrier-free-facilities
    '''

    url = "https://opendata.mtr.com.hk/data/mtr_bus_stops.csv"
    with requests.Session() as s:
        data = s.get(url)
        data = data.content.decode("utf-8")
        lines = data.splitlines()
        return lines

def mtr_bus_route_detail() -> list: 
    '''
    Save MTR bus routes csv from https://data.gov.hk/tc-data/dataset/mtr-data-routes-fares-barrier-free-facilities/resource/dfd4b454-e5e1-4ed8-b15d-99beb82f280c

    Details: https://data.gov.hk/tc-data/dataset/mtr-data-routes-fares-barrier-free-facilities
    '''

    url = "https://opendata.mtr.com.hk/data/mtr_bus_routes.csv"
    with requests.Session() as s:
        data = s.get(url)
        data = data.content.decode("utf-8")
        lines = data.splitlines()
        return lines

def mtr_lrt_route_stop_detail() -> list: 
    '''
    Save MTR bus routes csv to {dir} from https://data.gov.hk/tc-data/dataset/mtr-data-routes-fares-barrier-free-facilities/resource/15b7ac14-1d21-4ed5-b1a0-ca9f8802ee10

    Details: https://data.gov.hk/tc-data/dataset/mtr-data-routes-fares-barrier-free-facilities
    '''

    url = "https://opendata.mtr.com.hk/data/light_rail_routes_and_stops.csv"
    with requests.Session() as s:
        data = s.get(url)
        data = data.content.decode("utf-8")
        lines = data.splitlines()
        return lines

def kmb_route_detail() -> dict:
    '''
    Get KMB routes' stops list by route from https://data.gov.hk/en-data/dataset/hk-td-tis_21-etakmb/resource/9fc22f3a-5eae-4df8-9346-ba3e32a4f90d

    Details: https://data.gov.hk/en-data/dataset/hk-td-tis_21-etakmb

    @Exception
    - HTTPError
    '''

    url = "https://data.etabus.gov.hk/v1/transport/kmb/route/"
    response = requests.get(url)
    response.raise_for_status()
    data = json.loads(response.text)

    return data

def kmb_route_stop_detail(route: str, dir: Literal["inbound", "outbound"], services_type: int) -> dict:
    '''
    Get KMB stop defails by route from https://data.gov.hk/en-data/dataset/hk-td-tis_21-etakmb/resource/9fc22f3a-5eae-4df8-9346-ba3e32a4f90d

    Details: https://data.gov.hk/en-data/dataset/hk-td-tis_21-etakmb

    @Exception
    - HTTPError
    '''

    url = "https://data.etabus.gov.hk/v1/transport/kmb/route-stop/{rt}/{dir}/{st}".format(rt=route,dir=dir,st=services_type)
    response = requests.get(url)
    response.raise_for_status()
    data = json.loads(response.text)

    return data

def kmb_stop_detail(stop_id: str) -> dict:
    '''
    Get KMB stop defails by stop_id from https://data.gov.hk/en-data/dataset/hk-td-tis_21-etakmb/resource/8f60fda1-5720-4dbc-a41f-fa1e20b9b35e

    Details: https://data.gov.hk/en-data/dataset/hk-td-tis_21-etakmb

    @Exception
    - HTTPError
    '''

    url = "https://data.etabus.gov.hk/v1/transport/kmb/stop/{id}".format(id=stop_id)
    response = requests.get(url)
    response.raise_for_status()
    data = json.loads(response.text)

    return data

def mtr_train_route_stop_detail() -> list:
    '''
    Get KMB stop defails by stop_id from https://opendata.mtr.com.hk/data/mtr_lines_and_stations.csv

    Details: https://data.gov.hk/tc-data/dataset/mtr-data-routes-fares-barrier-free-facilities/resource/771d42e4-057d-4b4d-ae9e-08dbdf9ac371
    '''
    url = "https://opendata.mtr.com.hk/data/mtr_lines_and_stations.csv"
    response = requests.get(url)
    response.raise_for_status()
    
    with requests.Session() as s:
        data = s.get(url)
        data = data.content.decode("utf-8")
        lines = data.splitlines()
        return lines