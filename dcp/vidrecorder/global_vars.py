import configparser
import os

from utils.utils import str2bool
from utils.utils import convert_config_val
from utils.utils import isempty
from utils import fileutils

class Globals:
    """A singleton object keeping all of DCP's global variables"""

    def __init__(self):
        self.config_file = None
        self.config = None # reference parsed config file
        self.version = None
        self.dev_mode = False # dev_mode or prod_mode
        self.dev_opts = {}
        self.advanced = {
            'ping_rna_timeout_sec': 1, # default time to wait for a ping from an rna
            'restart_interval': 5.0, #default time to wait before restarting vlc if no data is flowing
        }
        self.paths = {
            'exedir': [],
            'viddir': [],
        }
        self.storage = {
            'reserve' : []
        }
        self.log = {
            'dir' : '',
            'group' : '',
            'permissions' : '',
            'logfile' : '',    # main log file
            'errfile' : '',    # error log file
            'dm_logfile' : '', # drive manager log file
        }

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        s = ""
        for (key, value) in self.__dict__.items():
            if (type(value) == dict):
                s += f"{key}:\n"
                for (k, v) in value.items():
                    s += f"   '{k}': {v} ({type(v)})\n"
            else:
                s += f"'{key}': {value}\n"
        s = s[0:-1]
        return s

g = Globals()

# Read config file
exe_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(exe_dir) # imperative that we change directory to location where dcp app main resides
g.config_file = os.path.join(exe_dir,'dcp_config.txt')
g.config = configparser.ConfigParser()
g.config.read_file(open(g.config_file))


# Set up paths
g.paths['exedir'] = exe_dir
g.paths['viddir'] = g.config.get('dcp_config','defaultSaveLocation')
g.paths['sessiondir'] = ''
g.paths['hdd'] = [
    g.config.get('dcp_config','disk_A_Location'),
    g.config.get('dcp_config','disk_B_Location'),
]

# Set up logging paths -- runtime logs will be stored in one of three places
#    1. Log dir provided in dcp_config.txt
#    2. In ibcs typical log location if /data_local exists otherwise...
#    3. In logs folder where dcp.py is located (<exedir>/logs)
logdir = g.config.get('logs','dir')
if isempty(logdir):
    dcp_data_root = '/data_local/dcp/data' # presumable ibcs location
    if not os.path.exists(dcp_data_root):
        dcp_data_root = g.paths['exedir']
    logdir = os.path.join(dcp_data_root,'logs')

g.paths['logfile'] = os.path.join(logdir,'dcp.log')
g.paths['errfile'] = os.path.join(logdir,'err.log')

# 0.2.0 addition: adding some global log vars for convenience
g.log['dir'] = logdir
g.log["group"] = g.config.get('logs','group')
g.log['permissions'] = int(g.config.get('logs','permissions'),8)
g.log['logfile'] = g.paths['logfile']
g.log['errfile'] = g.paths['errfile']

# Create log dir and set permissions/group if it doesn't already exist
fileutils.dcp_mkdir(g.log['dir'],g.log['group'],g.log['permissions'])

# Load and verify advanced settings
g.advanced['ping_rna_onlaunch'] = str2bool(g.config.get('advanced_settings','ping_rna_onlaunch'))

g.advanced['ping_rna_onlaunch_count'] = convert_config_val(
    config_val=g.config.get('advanced_settings','ping_rna_onlaunch_count'),
    convert2type='int',default_val=1,min_max=[1,10])

g.advanced['ping_rna_timeout_sec'] = convert_config_val(
    config_val=g.config.get('advanced_settings','ping_rna_timeout_sec'),
    convert2type='int',default_val=1,min_max=[1,10])

g.advanced['restart_interval'] = convert_config_val(
    config_val=g.config.get('advanced_settings','restart_interval'),
    convert2type='float',default_val=5.0,min_max=[0,100])

g.advanced['video_chapters_enabled'] = str2bool(g.config.get('advanced_settings','video_chapters_enabled'))

g.advanced['video_chapters_duration_in_minutes'] = convert_config_val(
    config_val=g.config.get('advanced_settings','video_chapters_duration_in_minutes'),
    convert2type='float',default_val=60,min_max=[0.5,None])

minAllowedOverlap = 0.5 # 30 seconds
maxAllowedOverlap = max(g.advanced['video_chapters_duration_in_minutes']/2.0, minAllowedOverlap)
g.advanced['video_chapters_overlap_in_minutes'] = convert_config_val(
    config_val=g.config.get('advanced_settings','video_chapters_overlap_in_minutes'),
    convert2type='float',default_val=minAllowedOverlap,min_max=[minAllowedOverlap,maxAllowedOverlap])

g.advanced['delete_chapters_per_ws'] = convert_config_val(
    config_val=g.config.get('advanced_settings','delete_chapters_per_ws'),
    convert2type='int',default_val=1,min_max=[1,None])

g.storage['reserve'] = convert_config_val(
         config_val=g.config.get('dcp_config','disk_reserve'),
         convert2type='float',default_val=0.5,min_max=[0,1])

# Setup dev global vars
g.dev_mode = g.config.get('dev_tools','devMode')
g.dev_opts = {
    'devLogCreator'          : str2bool(g.config.get('dev_tools','devLogCreator')),
    'devDirectory'           : str2bool(g.config.get('dev_tools','devDirectory')),
    'includePlayback'        : str2bool(g.config.get('dev_tools','includePlayback')),#TODO: Obsolete once playback is fully separated.
}

# print('_______________GLOBALS_______________')
# print(g)
