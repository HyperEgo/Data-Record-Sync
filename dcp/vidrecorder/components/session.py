import os
from datetime import datetime

from utils import utils

class Session:

    def __init__(self, dirpath):

        self.id        = None # (int) each session has a unique id number between 0-99
        self.datetime  = None # (datetime) the session was started
        self.basename  = None # (string) directory basename
        self.fullnames = [] # (list) of directory abspaths on each drive it exists

        self._parse_session_dirpath(dirpath)

    def add_session_fullpath(self,session_fullpath):
        if os.path.isabs(session_fullpath) and (session_fullpath not in self.fullnames):
            self.fullnames.append(session_fullpath)

    def spans_drives(self):
        return len(self.fullnames) > 1

    def _parse_session_dirpath(self,dirpath):
        self.basename  = os.path.basename(dirpath)
        self.id, self.datetime = parse_session_dirpath(self.basename)
        if os.path.isabs(dirpath):
            self.add_session_fullpath(dirpath)

    def _str_oneline(self,indent=0):
        spaces = indent * ' '
        output = \
f'''{spaces}{self.basename} | id: {self.id} | datetime: {self.datetime} | spans: {self.spans_drives()}'''
        return output
    
    def _str_long(self,indent=0):
        spaces = indent * ' '
        output = \
f'''{spaces}{self.basename} | id: {self.id} | datetime: {self.datetime} | spans: {self.spans_drives()}'''
        for f in self.fullnames:
            output = f"{output}\n{spaces}   {f}"
        return output

    def __str__(self):
        s = self.__dict__["name"] + ": "
        for (key, value) in self.__dict__.items():
            if (key == "name"):
                continue
            s += f"'{key}': '{value}',"
        s = s[0:-1]
        return s

#-------------------------------------------------------------------------------------------

def get_all_sessions(drives): # drives=g.paths['hdd']
    """Returns all session data info over the `drives` sorted by basename

    Args:
        drives (list of str, optional): abs path of drives. Defaults to g.paths['hdd'].

    Returns:
        [type]: [description]

    Note: # TODO: refactor this so it's not so confusing
        it returns a little data structure that isn't the same as what's
        returned by get_session_stats. Easy to get confused.
    """

    sessions = []
    min_session_id = 99999999
    max_session_id = 0

    for drive in drives:

        # session basename list, min session id, max session id
        sess_basenames,dmin,dmax = get_session_stats(drive)

        for sess_name in sess_basenames:
            sess_fullpath = os.path.join(drive,sess_name)
            sess = find_session(sess_name,sessions)
            if not sess:
                sess = Session(dirpath=sess_fullpath)
                sessions.append(sess)
            else:
                # the session basename exists on more the one drive, add it to the list
                sess.add_session_fullpath(sess_fullpath)

        min_session_id = min(min_session_id,dmin)
        max_session_id = max(max_session_id,dmax)

    # sessions = sorted(sessions, key=lambda d : d['basename'])
    sessions = sorted(sessions, key=lambda d : d.basename)
    return sessions, min_session_id, max_session_id

#-------------------------------------------------------------------------------------------
# HELPER FUNCTIONS

def get_session_stats(drive):
    """Returns list of all session basenames and min/max session ids on the drive

    Args:
        drive (str): abs path to drive

    Returns:
        tuple: session_basenames, min_session_id, max_session_id as (list,int,int)
    """
    session_basenames = []
    min_session_id = 99999999
    max_session_id = 0
    file_list = os.listdir(drive)
    for basename in file_list:
        if os.path.isdir(os.path.join(drive,basename)):
            session_id, _ = parse_session_dirpath(basename)
            if session_id == None:
                continue
            if session_id > max_session_id:
                max_session_id = session_id
            if session_id < min_session_id:
                min_session_id = session_id
            session_basenames.append(basename)
    session_basenames.sort()

    return session_basenames, min_session_id, max_session_id

def parse_session_dirpath(dirpath=None):
    """Parses session dirpath and returns the parts.

    Args:
        dirpath (str): abs path or basename of session directory

    Returns: tuple(int,datetime)
        session_id (int): session id, they range from 1-99
        session_datetime (datetime): date and time the session started

    Format: <session_id>_<date>_<timestamp>
        ex. 01_2022-Apr-27_06h52m16s
    """
    session_id = session_datetime = None
    if not dirpath: return

    # timestamp = f'{datetime.date.today().strftime("%Y-%b-%d")}_{time.strftime("%Hh%Mm%Ss", time.localtime())}'
    # session_dir_fullpath = f'{best_drive}/{(max_session_id+1):02}_{timestamp}'

    # TODO: validate dirpath is correct session format before proceeding
    try:
        basename = os.path.basename(dirpath)
        parts = basename.split('_')
        session_id = utils.str2int(parts[0])
        session_datetime = datetime.strptime(f'{parts[1]}_{parts[2]}',"%Y-%b-%d_%Hh%Mm%Ss")
    except:
        print(f"Failed to parse session dirpath: {dirpath}")

    return session_id, session_datetime


def find_session(sess_name, session_list):
    """Return the session with basename == sess_name inside of session_list

    Args:
        sess_name (str): session name we are searching for
        session_list (list of Session): list built in get_all_sessions

    Returns:
        sess_obj: if found, the session object associated with sess_name, otherwise None
    """
    sess_obj = None
    sess_obj = [val for i,val in enumerate(session_list) if val.basename == sess_name]
    return sess_obj[0] if sess_obj else None


