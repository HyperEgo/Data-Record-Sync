
import os
import configparser
from utils.utils import str2bool
from utils.utils import convert_config_val

class Globals:
    def __init__(self):
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
            'sdpdir': [],
            'rtlogs': [],
        }
        self.storage = {
            'reserve' : []
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
g.config = configparser.ConfigParser()
g.config.read_file(open(r'dcp_config.txt')) #TODO: May need to move the config file to a location separate from the source code.

# Set up paths
g.paths['exedir'] = os.path.dirname(os.path.realpath(__file__))
g.paths['viddir'] = g.config.get('dcp_config','defaultSaveLocation')
g.paths['sessiondir'] = ''
g.paths['rt']     = os.path.join(g.paths['exedir'],'.rt')
g.paths['sdpdir'] = os.path.join(g.paths['rt'] ,'sdp')
g.paths['rtlogs'] = os.path.join(g.paths['rt'],'rtlogs')
g.paths['logfile'] = os.path.join(g.paths['rtlogs'],'dcp.log')
g.paths['errfile'] = os.path.join(g.paths['rtlogs'],'err.log')
g.paths['hdd'] = [
    g.config.get('dcp_config','disk_A_Location'),
    g.config.get('dcp_config','disk_B_Location'),
]

# Verify dirs -- create them if they don't exist
if not os.path.exists(g.paths['rt']):
    os.mkdir(g.paths['rt'])
if not os.path.exists(g.paths['sdpdir']):
    os.mkdir(g.paths['sdpdir'])
if not os.path.exists(g.paths['rtlogs']):
    os.mkdir(g.paths['rtlogs'])

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

g.advanced['video_chunking_enabled'] = str2bool(g.config.get('advanced_settings','video_chunking_enabled'))

g.advanced['video_chunking_duration_in_minutes'] = convert_config_val(
    config_val=g.config.get('advanced_settings','video_chunking_duration_in_minutes'),
    convert2type='float',default_val=60,min_max=[0.5,None])

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

print('_______________GLOBALS_______________')

print(g)
