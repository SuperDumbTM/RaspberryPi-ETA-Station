#!/usr/bin/python
# -*- coding:utf-8 -*-
import importlib
import os
import sys
import argparse
import configparser
from src.config import configurator
from src.log.mylogger import Logger
from src.display.interface import DisplayABC

ROOT = os.path.dirname(__file__)

# flags
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', action="store_true", dest="is_config", 
                    help="Specify the path to save the display output (Default: tmp/output.bmp)")
# image
parser.add_argument('-i', '--save-image', action="store_true", dest="image_out", 
                    help="Save the display to image file.  Use -I, --image-path to specify other destination")
parser.add_argument('-I', '--image-path', default=os.path.join(ROOT, "tmp", "output.bmp"), type=str, dest="path_image", 
                    help="Specify the path to save the display output (Default: tmp/output.bmp)")
# verbose
parser.add_argument('-v', '--verbose', action="store_true", dest="verbose", 
                    help="Print execution details of the programs to terminal.  Specifying the log level to get more information")
# EPD
parser.add_argument('-d', '--dry-run', action="store_true", dest="dryrun", 
                    help="Run the program without updating the display.  Flags -i, -v, -l will be automatically set")
parser.add_argument('-r', '--rotate', default=0, type=int, dest="degree", 
                    help="Rotate the display output by <degree> degree")
    # log
args_log = parser.add_argument_group(title="Logging")
args_log.add_argument('-l', '--log', action="store_true", dest="log", 
                    help="Save the log to file.  Use -L, --log-dir to specify other destination (Default: log/)")
args_log.add_argument('-L', '--log-dir', default=os.path.join(ROOT, "log"), type=str, dest="dir_log", 
                    help="Specify the directory to save the log.  (Default: log/)")
args_log.add_argument('--log-level', default="warning", type=str.upper, choices=["DEBUG","INFO","WARNING","ERROR","CRITICAL"], dest="log_lv", 
                    help="Specify the log level for both stdout and fout (Default: [WARNING])")
    # partial
args_partial = parser.add_argument_group(title="Partial update", 
                                         description="normal is intended to use with crontab or other scheduling tool")
args_partial.add_argument('-p', '--partial', action="store_true", dest="partial", 
                    help="Update the display using partial update mode if supported")
args_partial.add_argument('-m', '--partial-mode', default="loop", type=str.lower, choices=["loop","normal"], dest="mode", 
                    help="")
args_partial.add_argument('-t', '--partial-interval', default=60, type=int, dest="interval", 
                    help="[loop] Update display every <interval> second (Default: 60s)")
args_partial.add_argument('-C', '--partial-cycle', default=10, type=int, dest="times", 
                    help="[loop] Update <times> times, then exits the program (Default 10 times)")


args = parser.parse_args()
epd: DisplayABC = None

def path_check():
    if not os.path.exists(os.path.join(ROOT, "conf", "epd.conf")):
        Logger.log.critical("epd.conf is missing")
        raise FileNotFoundError()
    if not os.path.exists(os.path.join(ROOT, "conf", "eta.conf")):
        Logger.log.critical("eta.conf is missing")
        raise FileNotFoundError("eta.conf")
    if not os.path.exists(os.path.join(ROOT, "font")):
        Logger.log.critical("font/ is missing")
        raise FileNotFoundError()
    if not os.path.exists(os.path.join(ROOT, "data")):
        Logger.log.warning("data/ is missing, reconstructing")
        os.makedirs(os.path.join(ROOT, "data"))
        os.makedirs(os.path.join(ROOT, "data", "route_data"))
        os.makedirs(os.path.join(ROOT, "data", "route_data", "kmb"))
        os.makedirs(os.path.join(ROOT, "data", "route_data", "mtr"))
        os.makedirs(os.path.join(ROOT, "data", "route_data", "mtr", "bus"))
        os.makedirs(os.path.join(ROOT, "data", "route_data", "mtr", "lrt"))

def obj_setup():   
    if not os.path.exists(os.path.join(ROOT, "conf", "epd.conf")):
        raise FileNotFoundError("epd.conf do not exists, consider using configurator recreate it.")
    else:
        Logger.log.debug("Parsing epd.conf")
        with open(os.path.join(ROOT, "conf", "epd.conf"), "r") as f:
            cparser = configparser.ConfigParser()
            cparser.read_file(f)
            try:
                size = cparser.get("epd", "size")
                brand = cparser.get("epd", "brand")
                model = cparser.get("epd", "model")
                test = "epd3in7_debug"
                test2 = "epd3in7_debug_timeonly"
                module = importlib.import_module(f"src.display.{brand}.{test}")
                
                return getattr(module, "CLS")(ROOT, int(size))
            except Exception as e:
                raise RuntimeError(f"[initialization]: {e}")

def main():
    global epd
    epd = obj_setup()
    
    if not args.dryrun:
        if args.partial and not epd.can_partial():
            Logger.log.error(f"{epd.__class__.__name__} do not support partial update")
            return
        
        epd.init()
        # if not args.partial:
        epd.clear()
    
    # get and draw ETA
    Logger.log.info("Drawing ETA information")
    epd.draw()
    
    # update display
    if not args.dryrun: 
        Logger.log.info(f"Displaying output to e-paper display")
        if args.partial:
            # partial update
            epd.partial_update(args.degree, args.interval, args.times, args.mode ,args.path_image)
        else:
            # full update
            epd.full_update(args.degree)
            
    # save image
    if args.dryrun or args.image_out or args.partial: 
        Logger.log.info(f"Saving output to {args.path_image}")
        epd.save_image(args.path_image)
    
    return 0


if __name__=='__main__':
    try:
        path_check()
        if not args.is_config:
            # set dry run
            if args.dryrun:
                args.verbose = True
                args.image_out = True
                args.log_lv = "DEBUG"
            # set log level 
            if args.verbose:
                Logger.verbose(getattr(Logger, args.log_lv))
                Logger.log.info(f"Log level is set to {args.log_lv}")
            main()
        else:
            configurator.Configurator(ROOT)
    except KeyboardInterrupt:
        Logger.log.info("")
    except Exception as e:
        Logger.log.error(f"Error occurrs during execution: {e}", exc_info=1)
    finally:
        if not args.dryrun and epd is not None: epd.exit()
        Logger.log.info("Exit")
