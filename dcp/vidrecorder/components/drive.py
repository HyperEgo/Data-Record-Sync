import os
import shutil
import threading

from global_vars import g
from utils import utils
from components.session import get_session_stats

class DriveStats:

    # class variables
    reserve_pct  = g.storage['reserve'] # pct of storage we are holding in reserve (not allowed to use)
    usable_pct   = 1-g.storage['reserve'] # pct of storage we ARE allowed to use
    warning_pct  = 0.7

    def __init__(self, drivepath, active_drivepath):
        """Class representing drive stats for a storage device on the dcp

        Args:
            drivepath (string): drivepath of drive
            active_drivepath (string): abspath of current drive being recorded to
        """

        # drive path stuff -- I can't decide what to name this shit yet
        self.basename  = None # (string) directory basename
        self.fullname  = None # (string) directory abspath
        self.abspath   = None # (string) directory abspath, same as fullname just a convenience
        self.drive     = None #TODO: remove this after integration? old stuff used this
        self.drivepath = None

        self._parse_drivepath(drivepath)

        # stat stuff
        self.active = False # is this the drive currently being written to
        self.stats = None # # as returned by shutil.disk_usage
        self.pct = dict(
            reserve = DriveStats.reserve_pct,
            usable  = DriveStats.usable_pct,
            warning = DriveStats.warning_pct
        )
        self.actual_capacity = 0 # available bytes to use after reserve is taken into account
        self.actual_pct_used = 0
        self.actual_pct_used_warning = False
        self.actual_pct_used_breach = False
        self.harvest_needed = False
        self.session_basenames = []
        self.available_bytes_gb = -1
        self.has_free_space = None
        self.min_session_id = -1
        self.max_session_id = -1

        self.calc_drive_stats(active_drivepath)

    def calc_drive_stats(self,active_drivepath):
        """Computes all drive stats at the time of call

        Args:
            active_drivepath (string): abspath of current drive being recorded to
        """
        shutil_stats = shutil.disk_usage(self.abspath)
        # usage(total=7620804153344, used=11235618816, free=7225476755456)
        actual_capacity = shutil_stats.total * DriveStats.usable_pct
        actual_pct_used = shutil_stats.used/actual_capacity
        available_bytes = actual_capacity * (1-actual_pct_used)
        available_bytes_gb = utils.bytesto(available_bytes,'gb')

        self.active = (self.abspath == active_drivepath)
        self.stats = shutil_stats
        self.actual_capacity = actual_capacity
        self.actual_pct_used = actual_pct_used
        self.actual_pct_used_warning = (actual_pct_used >= DriveStats.warning_pct)
        self.actual_pct_used_breach = (actual_pct_used >= 1)
        self.harvest_needed = (actual_pct_used >= 1)
        self.available_bytes_gb = available_bytes_gb
        self.has_free_space = self.actual_pct_used_breach

        # Add session stats for this drive
        session_basenames, min_session_id, max_session_id = get_session_stats(self.abspath)
        self.session_basenames = session_basenames
        self.min_session_id = min_session_id
        self.max_session_id = max_session_id

    def _parse_drivepath(self,drivepath):
        self.basename  = os.path.basename(drivepath)
        if os.path.isabs(drivepath):
            self.fullname = drivepath
            self.abspath = drivepath
            self.drive = drivepath
            self.drivepath = drivepath

    def print_drive_stat(self):
        print(self._str_long())

    def _str_long(self):
        drive_basename = self.basename
        stats = self.stats
        reserve_pct = f'{(self.pct["reserve"]*100):.2f}'
        actual_capacity_gb = f'{utils.bytesto(self.actual_capacity,"gb"):.2f}'
        actual_pct_used = f'{self.actual_pct_used*100:.2f}'
        actual_free_gb = f'{self.available_bytes_gb:.2f}'
        capacity_status = f'(warn,breach,harvest): {self.actual_pct_used_warning,self.actual_pct_used_breach,self.harvest_needed}'

        # this doesn't work in unit test for some reason, I think it's process related bullshit
        is_active = '(ACTIVE)' if self.active == True else '        '

        output = \
f'''
--------------------------------------------------------------------------------------
({actual_pct_used}%)
{drive_basename}: free {utils.bytesto(stats.free,"gb"):.2f} GB / used {utils.bytesto(stats.used,"gb"):.2f} GB / total {utils.bytesto(stats.total,"gb"):.2f} GB / {threading.current_thread().name}
     actual: ({actual_pct_used}%) / free_gb {actual_free_gb} GB / total {actual_capacity_gb} GB / reserve {reserve_pct}% / has_free_space: {self.has_free_space}
     warning at {self.pct["warning"]*100}% / {capacity_status}
     max_session_id: {self.max_session_id} / sessions: {self.session_basenames}
'''
        # for session_basename in self.session_basenames:
        #     output = f'{output}\n     {session_basename}'
        #     chapter_stats = DriveManager.get_chapter_stats(drive_info['drive'],session_basename)
        #     for chapter_stat in chapter_stats:
        #         output = f'{output}\n{cls.__chapter_stat_to_string_short2(chapter_stat,indent=8)}'

        return output

#-------------------------------------------------------------------------------------

def get_video_storage_stats(from_drives,active_drive):
    """Returns list of DriveStat with current status information for each drive.

    Args:
        from_drives (list of str or str, optional): list of all drive paths.
        active_drive (str): path to current active drive

    Returns:
        list of DriveStat: stats are calculated in DriveStat constructor
    """

    video_storage = []

    if type(from_drives) != list:
        from_drives = [from_drives]

    for drive in from_drives:
        drive_stat = DriveStats(drive,active_drive)
        video_storage.append(drive_stat)

    return video_storage

def find_drive_stat(drive_name,drive_stats):
    """Returns index and stats associated with drive_name in drive_stats list

    Args:
        drive_name (str): abs path of drive we are looking for
        drive_stats (list of dict): drive stats of all drives returned by get_video_storage_stats

    Returns: tuple
        idx (int): is index where drive_name was found in drive_stats
        dstat (dict): drive stat dict found in drive_stats (built in get_video_storage_stats)
    """
    idx = dstat = None
    for i,d in enumerate(drive_stats):
        if d.abspath == drive_name:
            dstat = d
            idx = i
            break
    return idx, dstat


def get_next_drive2(active_drive,drive_stats):
    """Returns next drive to use after `active_drive`.

    Args:
        active_drive (str): abs path to current active drive
        drive_stats (list[DriveStats]): drive stats of all drives returned by get_video_storage_stats

    Returns:
        dict: drive stats of next drive to start recording on
    """
    ndrives = len(drive_stats)
    idx, dstat = find_drive_stat(active_drive,drive_stats)
    return drive_stats[(idx+1)%ndrives] if (not idx == None) and idx >= 0 else None


def print_drive_stats(drive_stats):
    if type(drive_stats) == list:
        for d in drive_stats:
            d.print_drive_stat()
    else:
        drive_stats.print_drive_stat()
