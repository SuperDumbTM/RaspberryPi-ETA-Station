import json

def station_input():
    route = "615P"
    f_dir = "data/lrt/route_stops/"
    with open(f_dir+"routes.json","r",encoding="utf-8") as f:
        data = json.load(f)
        data[route]["details"]={}

        if (data[route].get("outbound",0)!=0):
            for inner in data[route]["outbound"]:
                inner["platform_id"]=int(input("current station - "+inner["name_ch"]+": "))
                pass
        print("-----")
        for inner in data[route]["inbound"]:
            inner["platform_id"]=int(input("current station - "+inner["name_ch"]+": "))
            pass

        with open(f_dir+"route_details.json","r",encoding="utf-8") as d:
            details = json.load(d)
            print(details[route]["details"])
            data[route]["details"]=details[route]["details"]
            
        
        with open(f_dir+route+".json", 'w+', encoding="utf-8") as j:
            j.write(json.dumps(data[route]))

def csv_to_json():
    f_dir = "data/lrt/"
    output = {}
    with open(f_dir+"light_rail_routes_and_stops.csv","r",encoding="utf-8") as f:
        f.readline()
        for line in f.readlines():
            args = line.split(",")
            route = args[0].strip("\"")

            output.setdefault(route,{})
            output[route].setdefault("inbound",[])
            output[route].setdefault("outbound",[])
            
            tmp = {
                "stop_code":args[2].strip("\""),
                "station_id":int(args[3].strip("\"")),
                "name_ch":args[4].strip("\""),
                "name_en":args[5].strip("\""),
                "seq":int(float(args[6].strip("\n")))
            }
            if (args[1].strip("\"")=="1"): output[route]["outbound"].append(tmp)
            if (args[1].strip("\"")=="2"): output[route]["inbound"].append(tmp)

    with open (f_dir+"route_stops/routes.json","w+",encoding="utf-8") as f:
        f.write(json.dumps(output))

station_input()