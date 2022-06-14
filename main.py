#!/usr/bin/python
# -*- coding:utf-8 -*-
import importlib
import os
import sys
import argparse
import configparser
from src.log.mylogger import Logger
from src.display.interface import DisplayABC

# path
picdir = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'pic')
tmpdir = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'tmp')
conf = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'conf')
libdir = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'lib')
logdir = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'log')
sys.path.append(libdir)

# flags
parser = argparse.ArgumentParser()
# image
parser.add_argument('-i', '--save-image', action="store_true", dest="image_out", 
                    help="Save the e-paper display output to \"tmp/\".  Use -I, --image-path to specify other destination")
parser.add_argument('-I', '--image-path', default="tmp/", type=str, dest="image_dir", 
                    help="Specify the path to save the e-paper display output.  (Default: \"conf/setting.conf\")")
# verbose
parser.add_argument('-v', '--verbose', action="store_true", dest="verbose", 
                    help="Print execution details of the programs to terminal.")
# log
parser.add_argument('-l', '--log', action="store_true", dest="log", 
                    help="Save the program log to \"log/\".  Use -L, --log-path to specify other destination")
parser.add_argument('-L', '--log-path', default="log/", type=str, dest="log_dir", 
                    help="Specify the path to save the log.  (Default: \"log/\")")
parser.add_argument('--log-level', default="warning", type=str.lower, choices=["debug","info","warning","error","critical"], dest="log_lv", 
                    help="Specify the log level for both stdout and fout.  (Default: [warning])")
# EPD
parser.add_argument('-x', '--dry-run', action="store_true", dest="dryrun", 
                    help="Run the program without printing the output to the display.  \nflags -i, -v, -l will be automatically set, and log level will be set to [debugpythj]")
parser.add_argument('-p', '--partial', default=None, type=int, dest="partial", 
                    help="Updating the e-paper display using partial update mode if supported (-p/--partial <pt update mode no>)")
parser.add_argument('-r', '--rotate', default=0, type=int, dest="degree", 
                    help="Rotating the output by -r/--rotate <degree>")


args = parser.parse_args()
epd: DisplayABC = None

# helper function
def obj_setup():    
    if not os.path.exists("conf/epd.conf"):
        Logger.log.error("conf/epd.conf do not exists")
        return None
    else:
        Logger.log.debug("parsing conf/epd.conf")
        with open("conf/epd.conf", "r") as f:
            cparser = configparser.ConfigParser()
            cparser.read_file(f)
            try:
                size = cparser.get("epd","size")
                brand = cparser.get("epd","brand")
                model = cparser.get("epd","model")
                test = "epd3in7 copy"
                test2 = "epd3in7 timeonly"
                module = importlib.import_module(f"src.display.{brand}.{test}")
                
                return getattr(module, "CLS")(int(size))
            except Exception as e:
                Logger.log.error(f"Exception occurrs during parsing conf/epd.conf: {e}")
                return None

def main():
    global epd
    epd = obj_setup()

    
    if epd is not None:
        if not args.dryrun:
            Logger.log.info("Initializing e-paper display")
            if args.partial is not None:
                if not epd.can_partial():
                    Logger.log.error(f"{epd.__class__.__name__} do not support partial update")
                    return
                else:
                    epd.set_mode(args.partial)
                    epd.init()
                    epd.clear()
            else:
                epd.init()
                epd.clear()
        
        Logger.log.info("Drawing ETA information")
        epd.draw()
        
        if args.dryrun or args.image_out: 
            Logger.log.info(f"Saving output to {args.image_dir}")
            epd.save_image()
        
        if not args.dryrun: 
            Logger.log.info(f"Displaying output to e-paper display")
            if args.partial is not None:
                epd.partial_update(args.degree)
            else:
                epd.full_update(args.degree)
    else:
        return



if __name__=='__main__':
    try:
        if not args.verbose:
            Logger.set_log_level("critical")
        else:
            Logger.set_log_level(args.log_lv)
        main()
    except Exception as e:
        Logger.log.error(f"Exception occurrs during executing main(): {e}")
    finally:
        if not args.dryrun and epd is not None: epd.exit()
        Logger.log.info("Exit")
