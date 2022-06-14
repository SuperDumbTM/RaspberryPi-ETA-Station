#!/usr/bin/python
# -*- coding:utf-8 -*-
import importlib
import os
import sys
import argparse
import configparser
from src.log.mylogger import Logger
from src.display.interface import DisplayABC

ROOTDIR = os.path.dirname(__file__)

# flags
parser = argparse.ArgumentParser()
# image
parser.add_argument('-i', '--save-image', action="store_true", dest="image_out", 
                    help="Save the e-paper display output to \"tmp/\".  Use -I, --image-path to specify other destination")
parser.add_argument('-I', '--image-path', default=os.path.join(ROOTDIR, "tmp", "output.bmp"), type=str, dest="image_dir", 
                    help="Specify the path to save the e-paper display output.  (Default: \"tmp/output.bmp\")")
# verbose
parser.add_argument('-v', '--verbose', action="store_true", dest="verbose", 
                    help="Print execution details of the programs to terminal.")
# log
parser.add_argument('-l', '--log', action="store_true", dest="log", 
                    help="Save the program log to \"log/\".  Use -L, --log-dir to specify other destination")
parser.add_argument('-L', '--log-dir', default=os.path.join(ROOTDIR, "log"), type=str, dest="log_dir", 
                    help="Specify the path to save the log.  (Default: \"log/\")")
parser.add_argument('--log-level', default="warning", type=str.upper, choices=["DEBUG","INFO","WARNING","ERROR","CRITICAL"], dest="log_lv", 
                    help="Specify the log level for both stdout and fout.  (Default: [warning])")
# EPD
parser.add_argument('-d', '--dry-run', action="store_true", dest="dryrun", 
                    help="Run the program without printing the output to the display.  \nflags -i, -v, -l will be automatically set, and log level will be set to [debugpythj]")
parser.add_argument('-p', '--partial', default=None, type=int, dest="partial", 
                    help="Updating the e-paper display using partial update mode if supported (-p/--partial <pt update mode no>)")
parser.add_argument('-t', '--partial-interval', default=60, type=int, dest="interval", 
                    help="Only for partial update.  Update display every -t/--partial-interval <second>.  Defaule: 60s")
parser.add_argument('-C', '--partial-cycle', default=10, type=int, dest="times", 
                    help="Only for partial update.  Update -c/--partial-cycle <times>, then exits the program.  Default 10 times")
parser.add_argument('-P', '--partial-image', default=None, type=str, dest="image_path", 
                    help="Image path for partial update.")
parser.add_argument('-r', '--rotate', default=0, type=int, dest="degree", 
                    help="Rotating the output by -r/--rotate <degree>")


args = parser.parse_args()
epd: DisplayABC = None

def obj_setup():    
    if not os.path.exists("conf/epd.conf"):
        Logger.log.error("epd.conf do not exists, consider using configurator recreate it.")
        return None
    else:
        Logger.log.debug("Parsing epd.conf")
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
                
                return getattr(module, "CLS")(ROOTDIR, int(size))
            except Exception as e:
                Logger.log.error(f"Error occurrs during initialization: {e}")
                return None

def main():
    global epd
    epd = obj_setup()
    
    if epd is not None:
        # init EPD
        if not args.dryrun:
            if args.partial is not None:
                if not epd.can_partial():
                    Logger.log.error(f"{epd.__class__.__name__} do not support partial update")
                    return
                else:
                    # partial update
                    epd.set_mode(args.partial)
                    epd.init()
                    epd.clear()
            else:
                # full update
                epd.init()
                epd.clear()
        else:
            Logger.set_log_level('info')
        
        # get and draw ETA
        Logger.log.info("Drawing ETA information")
        epd.draw()
        
        # save image
        if args.dryrun or args.image_out: 
            Logger.log.info(f"Saving output to {args.image_dir}")
            epd.save_image(args.image_dir)
        
        if not args.dryrun: 
            Logger.log.info(f"Displaying output to e-paper display")
            if args.partial is not None:
                # partial update
                epd.partial_update(args.degree, args.interval, args.times, args.image_path)
            else:
                # full update
                epd.full_update(args.degree)
    else:
        return



if __name__=='__main__':
    try:
        # set dry run
        if args.dryrun:
            args.verbose = True
            args.image_out = True
        
        # set log level 
        if not args.verbose:
            Logger.set_log_level(Logger.CRITICAL)
        else:
            Logger.set_log_level(getattr(Logger, args.log_lv))
            
        main()
    except Exception as e:
        Logger.log.error(f"Error occurrs during execution: {e}")
    finally:
        if not args.dryrun and epd is not None: epd.exit()
        Logger.log.info("Exit")
