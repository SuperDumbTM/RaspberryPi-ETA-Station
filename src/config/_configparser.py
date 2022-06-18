import configparser
import os

ROOT = os.getcwd() 

class ConfigParser:

    __conf: dict # config data in dictionary format
    __path: str # path to config file

    def __init__(self, path: str) -> None:
        self.__path = path
        self.__conf = self.__conf_to_dict()
        
    def __conf_to_dict(self) -> dict:
        output = {}
        parser = configparser.ConfigParser()
        if os.path.exists(self.__path):
            parser.read(self.__path)
            
            for section in parser.sections():
                output[section] = {}
                for key in parser.options(section):
                    output[section][key] = parser[section][key]
            return output
        else:
            return {}

    def set_path(self, path: str):
        if os.path.exists(path):
            self.__path(path)
        else:
            raise FileNotFoundError(f"{path} do not exists.")

    def get_conf(self) -> dict:
        return self.__conf
    
    def add_opt(self, key: str, opt: str, val):
        """add option to a section. if section not exists, create

        Args:
            key (str): section name
            opt (str): option name
            val (_type_): option value
        """
        self.__conf.setdefault(key, {})
        self.__conf[key][opt] = str(val)
        
    def add_opts(self, key: str, val: dict):
        """add option to a section

        Args:
            key (str): section name
            val (dict): {option name: value}
        """
        self.__conf[key] = {str(k):str(v) for k,v in val.items()}

    def add_section(self, key: str, overwirte: bool = False):
        """add new section with options to config file, 
        
        clear options when key already exists if overwirte is set to True

        Args:
            key (str): section name
            val (dict): options
        """
        if overwirte:
            self.__conf[key] = {}
        else:
            self.__conf.setdefault(key, {})
    
    def remove_section(self, key: str):
        """remove a section

        Args:
            key (str): name/key of the section
        """
        self.__conf.pop(key)

    def set_section_val(self, key: str, new_val: dict):
        """change `key`'s value"""
        self.__conf[key] = {str(k):str(v) for k,v in new_val.items()}

    def read(self):
        """read again (refresh)"""
        self.__conf = self.__conf_to_dict()

    def write(self):
        """write changes to `self.path`"""
        parser = configparser.ConfigParser()
        print(self.__conf)
        parser.read_dict(self.__conf)

        with open(self.__path, 'w') as f:
            parser.write(f)

if __name__ == "__main__":
    c = ConfigParser(ETA_CONF_PATH)
    print(c.get_conf())
    c.add_section("3", {"k1":"v1", "k2":"v2"})
    c.add_section("4", {"k1":"v1", "k2":"v2"})
    c.add_section("5", {"k1":"v1", "k2":"v2"})
    c.write()
    
