import configparser
import json


class Epdselector:
    
    @staticmethod
    def select_epd(fpath: str) -> tuple:
        """
        Args:
            fpath (str): path to `epd_list.json` (supported epd list)

        Returns:
            tuple: (brand, model)
        """
        with open(fpath, "r") as f:
            # epd brand
            epd_list: dict = json.load(f)
            for idx, _brand in enumerate(epd_list.keys()):
                print(f"[{idx}] {_brand}")
            
            _input = input("請選擇墨水屏 (e-paper) 牌子: ")
            while _input not in str(tuple(range(len(epd_list.keys())))):
                _input = input("輸入無效，請重新選擇: ")
            brand = list(epd_list.keys())[int(_input)]
            # epd model
            for idx, _model in enumerate(epd_list[brand]):
                print(f"[{idx}] {_model}")
            _input = input("請選擇墨水屏 (e-paper) 型號: ")
            while _input not in str(tuple(range(len(epd_list[brand])))):
                _input = input("輸入無效，請重新選擇: ")
            model = epd_list[brand][int(_input)]
        
        return (brand, model)
    
    @staticmethod
    def select_display_size(fpath: str, model: str) -> int:
        # parser = configparser.ConfigParser()
        # parser.read(fpath)
        
        size_list = {
            '1':1,
            '2':2,
            '3':3,
        }
        
        for idx, _size in size_list.items():
            print(f"[{idx}] {_size}")
        _input = input("請選擇: ")
        while(_input not in size_list.keys()):
                _input = input("輸入無效，請重新選擇: ")
        
        # deprecated      
        if _input == "4":
            _input = input("請輸入數量: ")
            while _input not in str(tuple(range(1, int(size_list['3']) + 1))):
                _input = input("輸入無效，請重新選擇: ")
            return int(_input)
        else:
            return int(size_list[_input])