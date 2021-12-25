import os
import sys
import getopt
import configparser

import tkinter as tk

from global_vars import g
from WorkstationDataRecorder_GUI import WorkstationDataRecorder_GUI
from PlaybackWindow_GUI import PlaybackWindow_GUI

import utils.vidlogging as vidlogging

application_name = "Workstation Recorder"
version_code = "0.1.5"
version_config = g.config.get('version_info','versionNumber')

# Setup loggers
logger = vidlogging.get_logger(__name__,filename=g.paths['logfile'])

# Make sure viddir works
if not os.path.exists(g.paths['viddir']) or not os.path.isdir(g.paths['viddir']):
    logger.error(f'''
ERROR: defaultSaveLocation in config file does not exist or is not directory.
Open file 'dcp_config.txt' and alter 'defaultSaveLocation' line
''')
    sys.exit(2)
    
# Check version numbers and make sure everything is good to go, exit otherwise
if (version_code != version_config):
    logger.error(f'version numbers between config file ({version_config}) and code ({version_code}) DO NOT MATCH')
    sys.exit(2)
g.version = version_code
# --------------------------------------------------------------------------------------------

def get_usage():
    usage = f'''
   Usage: python3 app.py [options]

    -v, --version             prints version number
    -h, --help                prints help information
    -p, --playback            runs only the playback module
    -r, --recorder            runs the full record/playback application

   Note: running with no options will default to --recorder mode
            '''
    return usage

def main(argv):

    try:
        opts, args = getopt.getopt(argv,"vhpr",["version","help","playback","recorder"])
    except getopt.GetoptError as e:
        print(e)
        print(get_usage())
        sys.exit(2)

    if (len(opts) == 0):
        run_app(use_full_gui=True)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(get_usage())

        elif opt in ('-v', '--version'):
            print(f'{application_name} -- Version: {version_config}')

        elif opt in ('-r', '--recorder'):
            run_app(use_full_gui=True)
            return

        elif opt in ('-p', '--playback'):
            if(g.dev_opts['includePlayback']):
                run_app(use_full_gui=False)
            else:
                print('This version does not support the playback module.')
            return

def run_app(use_full_gui=True):
    logger.info("----------------------------------------------------")
    logger.info(f"{application_name} executed")
    logger.info("----------------------------------------------------")
    root = tk.Tk()
    if use_full_gui:
        app = WorkstationDataRecorder_GUI(root,g.config)
    else:
        app = PlaybackWindow_GUI(root,g.config)
    root.mainloop()

if __name__ == "__main__":
    main(sys.argv[1:])
