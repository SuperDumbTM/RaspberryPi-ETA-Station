import json
import os
import configparser
import routeselector as rts
from eta import route_details as dets
from eta import details_update as upd

KMB_LANG_TRANS = {'tc': "tc", 'sc': "sc", 'en': "en"}
MTR_LRT_LANG_TRANS = {'tc': "ch", 'sc': "ch", 'en': "en"}
MTR_BUS_LANG_TRANS = {'tc': "zh", 'sc': "zh", 'en': "en"}


class Configurator:
    def __init__(self, lang: str = "tc") -> None:
        
        self.config_dir = "conf/setting.conf"
        self.intput_count = 0
        self.eta_row_size = 0
        self.kmb_lang = KMB_LANG_TRANS[lang]
        self.mtr_lrt_lang = MTR_LRT_LANG_TRANS[lang]
        self.mtr_bus_lang = MTR_BUS_LANG_TRANS[lang]
        self.config_parser = configparser.ConfigParser()

        # if not os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)),self.config_dir)):
        #     with open(self.config_dir,'r+'):
        #         pass

        #del setting_reader
        self.func_list = {
            "1":"重新設定/新增設定",
            "2":"查看現有設定",
            "3":"修改現有設定",
            "4":"刪除設定"
        }
        self.eta_co_list = {
            '1':"九巴",
            #'2':"新巴/城巴",
            #'3':"港鐵-重鐵",
            '4':"港鐵-輕鐵",
            '5':"港鐵-巴士"
        }
        self.lang_list={
            '1':("tc","繁體中文"),
            '2':("en","English")
        }    
    
    def __epd_selector(self) -> None:
        with open("data/epd_list.json","r") as f:
            epd_list = json.load(f)
        
        # brand
        for key in epd_list.keys():
            print("[{idx}] {mod}".format(idx=list(epd_list.keys()).index(key), mod=key))
        self.brand = input("請選擇墨水屏 (e-paper) 牌子: ")
        while True:
            try:
                if int(self.brand) < 0 or int(self.brand) > len(epd_list.keys())-1:
                    self.brand = input("輸入無效，請重新選擇: ")
                else: break
            except ValueError:
                self.brand = input("輸入無效，請重新選擇: ")
        self.brand = list(epd_list.keys())[int(self.brand)]
        
        # model
        for i in range(len(epd_list[self.brand])):
            print("[{idx}] {mod}".format(idx=i, mod=epd_list[self.brand][i]))
        self.model = input("請選擇墨水屏 (e-paper) 型號: ")
        while True:
            try:
                self.model = int(self.model)
                if (self.model < 0 or self.model > len(epd_list[self.brand])-1) or epd_list[self.brand][self.model] not in epd_list[self.brand]:
                    self.model = input("輸入無效，請重新選擇: ")
                else: break
            except ValueError:
                self.model = input("輸入無效，請重新選擇: ")
        self.model = epd_list[self.brand][self.model]
        
        epd_setting_dir = "conf/"+self.brand+"_size.conf"
        setting_reader = configparser.ConfigParser()
        setting_reader.read(epd_setting_dir)
        self.size_list = {
            '1':setting_reader.get(self.model,"s"),
            '2':setting_reader.get(self.model,"m"),
            '3':setting_reader.get(self.model,"l"),
            '4': "自訂"
        }

    def __func_selector(self) -> None:
        print("功能: ")
        for key,val in self.func_list.items():
            print("[{0}] {1}".format(key,val))
        input_func = input("請選擇: ")
        while(input_func not in self.func_list.keys()):
                input_func = input("輸入無效，請重新選擇: ")

        if input_func == '1':
            self.new_conf()
        elif input_func == '2':
            self.view_conf()
        elif input_func == '3':
            self.mod_conf()
        elif input_func == '4':
            self.clear_conf()
    
    def __selector_lang(self) -> str:
        for key,val in self.lang_list.items():
            print("[{0:}] {1}".format(key,val[1]))

        input_lang = input("請選擇題示語言: ")
        while (input_lang not in self.lang_list.keys()):
            input_lang = input("輸入無效，請重新選擇: ")
        return self.lang_list[input_lang][0]
        
    def __etaco_selector(self) -> dict:
        for key,val in self.eta_co_list.items():
            print("[{0}]  {1}".format(key,val))

        input_co = input("請選擇: ")
        while(input_co not in self.eta_co_list.keys()):
            input_co = input("輸入無效，請重新選擇: ")
                            
        if (input_co=='1'): # KMB
            return rts.kmb_conf(self.kmb_lang)
        elif (input_co=='2'): # CTB/NWB
            pass
        elif (input_co=='3'): # MTR-HRT
            pass
        elif (input_co=='4'): # MTR-LRT
            return rts.mtr_lrt_conf(self.mtr_lrt_lang)
        elif (input_co=='5'): # MTR-BUS
            return rts.mtr_bus_conf(self.mtr_bus_lang)

    def __set_row_size(self) -> str:
        if self.eta_row_size <= int(self.size_list['3']):
            return "L"
        elif self.eta_row_size <= int(self.size_list['2']):
            return "M"
        else:
            return "S"

    def new_conf(self):
        # select eta display row qty
            # backup conf file
            with open(self.config_dir,'r') as f:
                with open(self.config_dir+".bak",'w') as g:
                    g.writelines(f.readlines())

            try:
                self.config_parser.add_section("epd")
                self.__epd_selector()
                self.config_parser.set("epd","brand",self.brand)
                self.config_parser.set("epd","model",self.model)
                
                print(self.brand+"-"+self.model+" 預報顯示數量: ")
                print("選項|數量")
                for key,val in self.size_list.items():
                    print("[{0}]   {1}".format(key,val))

                self.eta_row_size = input("請選擇: ")
                while self.eta_row_size not in self.size_list.keys():
                    self.eta_row_size = input("輸入無效，請重新選擇: ")

                if self.eta_row_size == "4":
                    self.eta_row_size = input("請輸入數量: ")
                    while True:
                        try:
                            if int(self.eta_row_size) > int(self.size_list["1"]) or int(self.eta_row_size)<=0: # celling
                                self.eta_row_size = input("輸入無效，請重新選擇: ")
                            else: break
                        except ValueError:
                            self.eta_row_size = input("輸入無效，請重新選擇: ")
                    self.eta_row_size = int(self.eta_row_size)
                            
                else:
                    self.eta_row_size = int(self.size_list[self.eta_row_size])
                self.config_parser.set("epd","size",self.__set_row_size())

                # select eta co.
                open(self.config_dir, 'w').close() # clear file content
                while self.intput_count < self.eta_row_size:   
                    self.config_parser[self.intput_count] = self.__etaco_selector()
                    self.intput_count += 1
                
            except (KeyboardInterrupt, Exception):
                os.remove(self.config_dir)
                os.rename(self.config_dir+".bak",self.config_dir)
                #self.config_parser.write(open(self.config_dir,"w"))
            else:
                print(self.config_parser.sections())
                print(self.config_parser.options("epd"))
                self.config_parser.write(open(self.config_dir,"w"))
                os.remove(self.config_dir+".bak")
            finally:
                self.view_conf()

    def __get_kmb_dsrpt(self, route: str, dir: str, services_type: int) -> str:
        dir_transalation = {'outbound': "O",'inbound': "I"}
        try:
            with open(upd.KMB_DATA_DIR,'r',encoding="utf-8") as f:
                data = json.load(f)['data']
                orig = data[route][dir_transalation[dir]][str(services_type)]["orig_"+self.kmb_lang]
                dest = data[route][dir_transalation[dir]][str(services_type)]["dest_"+self.kmb_lang]
                return orig+"→"+dest
        except:
            return "err"

    def __get_mtr_lrt_dsrpt(self, route: str, dir: str) -> str:
        orig = dets.get_mtr_lrt_orig(route,dir,self.mtr_lrt_lang)
        dest = dets.get_mtr_lrt_orig(route,dir,self.mtr_lrt_lang)
        return orig+"→"+dest
    
    def __get_mtr_bus_dsrpt(self, route: str, dir: str) -> str:
        orig = dets.get_mtr_bus_orig(route,dir,self.mtr_bus_lang)
        dest = dets.get_mtr_bus_dest(route,dir,self.mtr_bus_lang)
        return orig+"→"+dest

    def view_conf(self):
        self.config_parser.read_file(open(self.config_dir,"r"))
        for sec in self.config_parser.sections():
            if not sec == "epd":
                co = self.config_parser[sec]['eta_co']
                if co == "kmb":
                    rt = self.config_parser[sec]['route']
                    dir = self.config_parser[sec]['dir']
                    st = self.config_parser[sec]['services_type']
                    seq = self.config_parser[sec]['seq']

                    dsrpt = self.__get_kmb_dsrpt(rt,dir,st)
                    stop = dets.get_kmb_stop_name(rt,dir,int(seq),int(st),self.kmb_lang)
                elif co == "ctb/nwb": #TODO: ctb/nwb
                    pass
                elif co == "mtr_hrt": #TODO: mtr_hrt
                    pass
                elif co == "mtr_lrt":
                    rt = self.config_parser[sec]['route']
                    dir = self.config_parser[sec]['dir']
                    palt = self.config_parser[sec]['platform_id']
                    stat = self.config_parser[sec]['station_id']

                    dsrpt = self.__get_mtr_lrt_dsrpt(rt,dir)
                    stop = dets.get_mtr_lrt_stop_name(stat,self.mtr_lrt_lang)
                elif co == "mtr_bus":
                    rt = self.config_parser[sec]['route']
                    dir = self.config_parser[sec]['dir']
                    _stop = self.config_parser[sec]['stop_id']

                    dsrpt = self.__get_mtr_bus_dsrpt(rt,dir)
                    stop = dets.get_mtr_bus_stop_name(rt,dir,_stop,self.mtr_bus_lang)

                print("{sec}: {rt:<13} {dsrpt} @ {stop}".format(sec=sec, rt=rt+" ("+co+")", dsrpt=dsrpt, stop=stop))
            elif sec == "epd":
                print("墨水屏 (epaper) 型號: ", self.config_parser[sec]["brand"], "-", self.config_parser[sec]["model"])
                print("預報數目: {0} ({1})".format(len(self.config_parser.sections())-1,self.config_parser[sec]['size']))
                print("-"*15)
            
    def mod_conf(self):
        #self.config_parser.read_file(open(self.config_dir,"r+"))
        
        print("[0] 修改現有項目")
        print("[1] 刪除現有項目")
        input_act = input("請選動作: ")
        while input_act not in ("0","1"):
            input_act = input("輸入無效，請重新選擇: ")

        self.view_conf()
        input_sec = input("請選擇修改項目: ")
        while input_sec not in self.config_parser.sections():
            input_sec = input("輸入無效，請重新選擇: ")

        with open(self.config_dir,'w+') as f: # clear section first
            #self.config_parser.read_file(f)
            self.config_parser.remove_section(input_sec)
            f.seek(0)
            f.truncate()

            if input_act != "1":
                for key,val in self.__etaco_selector().items():
                    self.config_parser.set(input_sec,key,str(val))
            self.config_parser.write(f)
            #self.config_parser.write(open(self.config_dir,"w"))

        print("已完成修改:\n")
        self.view_conf()

    def clear_conf(self):
        open(self.config_dir, 'w').close()

conf = Configurator()
conf.view_conf()