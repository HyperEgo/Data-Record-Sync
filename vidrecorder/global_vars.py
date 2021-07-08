
import os
import configparser

class Globals:
    def __init__(self):
        self.config = None # reference parsed config file
        self.log_manager = None
        self.version = None
        self.dev_mode = False # dev_mode or prod_mode
        self.dev_opts = {}
        self.advanced = {}
        self.paths = {
            'exedir': [],
            'viddir': [],
            'sdpdir': [],
            'rtlogs': [],
        }

g = Globals()

# Read config file
g.config = configparser.ConfigParser()
g.config.read_file(open(r'dcp_config.txt'))

# Set up paths
g.paths['exedir'] = os.path.dirname(os.path.realpath(__file__))
g.paths['viddir'] = g.config.get('dcp_config','defaultSaveLocation')
g.paths['rt']     = os.path.join(g.paths['exedir'],'.rt')
g.paths['sdpdir'] = os.path.join(g.paths['rt'] ,'sdp')
g.paths['rtlogs'] = os.path.join(g.paths['rt'],'rtlogs')
g.paths['logfile'] = os.path.join(g.paths['rtlogs'],'dcp.log')
g.paths['hdd'] = [
    g.config.get('dcp_config','disk_A_Location'),
    g.config.get('dcp_config','disk_B_Location'),
]

g.advanced['ping_rna_onlaunch'] = g.config.get('advanced_settings','ping_rna_onlaunch') == "1"
g.advanced['ping_rna_timeout_sec'] = int(g.config.get('advanced_settings','ping_rna_timeout_sec'))

# Setup dev global vars
g.dev_mode = g.config.get('dev_tools','devMode')
g.dev_opts = {
    'devLogCreator'          : g.config.get('dev_tools','devLogCreator'),
    'devDirectory'           : g.config.get('dev_tools','devDirectory'),
    'devSize'                : g.config.get('dev_tools','devSize'),
    'devEditableSaveLocation': g.config.get('dev_tools','devEditableSaveLocation'),
    'includePlayback'        : g.config.get('dev_tools','includePlayback')
}

print('_______________GLOBALS_______________')
