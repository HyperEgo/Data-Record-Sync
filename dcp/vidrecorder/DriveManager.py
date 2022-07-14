import os
import threading
import shutil
from datetime import datetime

import utils.vidlogging as vidlogging
from global_vars import g
from utils import utils
from components.session import Session
from components.session import get_all_sessions
from components.session import get_session_stats

# logger = vidlogging.get_logger(__name__,filename=g.paths['logfile'])
g.log['dm_logfile'] = os.path.join(g.log['dir'],'dm.log')
logger = vidlogging.get_logger(__name__,filename=g.log['dm_logfile'])

class DriveManager():

    # class variables
    reserve_pct  = g.storage['reserve'] # pct of storage we are holding in reserve (not allowed to use)
    usable_pct   = 1-g.storage['reserve'] # pct of storage we ARE allowed to use
    warning_pct  = 0.7

    @classmethod
    def parse_chapter_file_name(cls,filename: str):
        """Parse format <wsid>_<chaptid>_<dt>.mp4 into it's components

           Args:
               filename: abs or rel path to chapter file

           Returns: tuple(str,int,float)
               wsid (str)    : workstation id
               chaptid (int) : chapter id
               dt (float)    : overlap time (not currently implemented)

           Example:
               filename = 'ws03_1234_3.6.mp4'
               wsid,chaptid,dt = DriveManager.parse_chapter_file_name(filename)
               # returns wsid = ws03, chaptid = 1234, dt = 3.6

        """
        wsid = None; chaptid = None; dt = None
        if filename:
            basename = os.path.basename(filename)
            parts = basename.split('_')
            if len(parts) == 1: # old filename format <wsid>.mp4
                s = parts[0].split('.')
                wsid = s[0]
            elif len(parts) == 3: # new filename format <wsid>_<chaptid>_<dt>.mp4
                wsid = parts[0]
                chaptid = int(parts[1])
                dt = float(parts[2][0:parts[2].rfind('.')])
        return wsid, chaptid, dt

    @classmethod
    def delete_oldest_files(cls,n_workstations,n_chapters_per_ws=g.advanced['delete_chapters_per_ws']):
        """Deletes a batch of the oldest chapter files over ALL the drives

        Args:
            n_workstations (int): number of recording workstations
            n_chapters_per_ws (int, optional): number of chapters to delete per workstation.
                                               Defaults to g.advanced['delete_chapters_per_ws'].

        Returns:
            Nothing

        Note:
            The amount of files that will be deleted is computed like so....
            total_chapters_to_delete = n_chapters_per_ws * n_workstations
        """

        total_chapters_to_delete = n_chapters_per_ws * n_workstations

        # Get all of the sessions spanning all drives
        drive_dirs = g.paths['hdd']
        sessions, min_session_id, max_session_id = get_all_sessions(drive_dirs) # returns sorted by basename

        # Case 1: if no sessions --> return do nothing
        if not sessions:
            return

        active_session_dir = sessions[-1].basename
        session_cnt = len(sessions)

        # Case 2: One session. Delete oldest files in session
        if (session_cnt == 1):

            # Get sorted (by creation time) list of tuples of all chapter files over all drives for active_session
            chapter_list = cls.get_chapters_in_session(active_session_dir)

            # delete oldest chapter sets on this drive
            logger.info(f'n_workstations: {n_workstations}')
            logger.info(f'n_chapters_per_ws: {n_chapters_per_ws}')
            logger.info(f'total_chapters_to_delete: {total_chapters_to_delete}')
            for tpl in chapter_list[0:total_chapters_to_delete]:
                p = tpl[1]
                logger.info(f' >>>>>>>>> Deleting File : {tpl}')
                p.unlink()

        # Case 3: Multiple sessions. Delete oldest session dirs until enough space has been released 
        elif (session_cnt > 1):
            oldest_session = sessions[0]
            delete_list = oldest_session.fullnames
            for directory in delete_list:
                logger.info(f' >>>>>>>>> Deleting Session Directory: {directory}')
                shutil.rmtree(directory)
            return

        logger.debug(f' Drives: {drive_dirs}')
        logger.debug(f' ==== Sessions ==== cnt: {len(sessions)} -- min: {min_session_id} -- max: {max_session_id}')
        for sess in sessions:
            logger.debug(sess._str_long(indent=3))
        #    logger.debug(f"   {sess_data['basename']} -- id: {sess_data['id']} -- startime: {sess_data['datetime']} -- spans: {sess_data['spans']} -- {sess_data['fullnames']}")
        logger.debug(f'active_session_dir: {active_session_dir}')

    @classmethod
    def make_free_space(cls,active_drive,n_workstations,n_chapters_per_ws=g.advanced['delete_chapters_per_ws']):

        # Free up some space
        cls.delete_oldest_files(n_workstations,n_chapters_per_ws)

        # Get current state of ALL the drives
        drive_stats = cls.get_video_storage_stats(active_drive)

        # Figure out which drive stat is the active one
        _ , active_dstat = cls.find_drive_stat(active_drive,drive_stats)

        # Check the active_dstat. If there is free space then return it
        if active_dstat['has_free_space']:
            logger.debug(f"make_free_space() returning active_dstat['drive']: {active_dstat['drive']}")
            return active_dstat['drive']

        # Active drive is full. Find the next drive to write to.
        next_dstat = cls.get_next_drive2(active_drive,drive_stats)

        # Check the next_dstat. If there is free space then return it
        if next_dstat['has_free_space']:
            logger.debug(f"make_free_space() returning next_dstat['drive']: {next_dstat['drive']}")
            return next_dstat['drive']

        # If we get this far this no free space anywhere. Let's free more space
        return cls.make_free_space(active_drive,n_workstations,n_chapters_per_ws)


    @classmethod
    def get_free_space(cls,drive_stat,n_workstations):
        """Returns free space info of drive represented by `drive_stat`

        Args:
            drive_stat (dict): dict returned by get_video_storage_stats
            n_workstations (int): currently unused # TODO: remove this?

        Returns: tuple (int,bool)
            bytes_available_gb (int): number of free bytes on the drive
            has_free_space (bool): True if free space exists, False otherwise
        """

        if isinstance(drive_stat,str): # assume its a drive path instead of drive_stat
            pass

        actual_capacity = drive_stat['actual_capacity']
        actual_pct_used = drive_stat['actual_pct_used']

        bytes_available = actual_capacity * (1-actual_pct_used)
        bytes_available_gb = utils.bytesto(bytes_available,'gb')

        has_free_space = not drive_stat['actual_pct_used_breach']

        return bytes_available_gb, has_free_space


    @classmethod
    def get_video_storage_stats(cls,active_drive,from_drives=g.paths['hdd']):
        """Returns list of dicts with current status information for each drive.

        Args:
            active_drive (str): path to current active drive
            from_drives (list of str or str, optional): list of all drive paths. Defaults to g.paths['hdd'].

        Returns:
            list of drive stats: drive stats built manually below, should refactor to it's own class
        """

        video_storage = []

        if type(from_drives) != list:
            from_drives = [from_drives]
        hdd = from_drives

        for drive in hdd:
            drive_stats = shutil.disk_usage(drive)
            # usage(total=7620804153344, used=11235618816, free=7225476755456)
            actual_capacity = drive_stats.total * DriveManager.usable_pct
            actual_pct_used = drive_stats.used/actual_capacity
            session_basenames, min_session_id, max_session_id = get_session_stats(drive)

            # TODO: refactor this into it's own class
            drive_info = {
                'drive': drive, # path to drive
                'active': drive == active_drive, # is this the drive currently being written to?
                'stats': drive_stats, # as returned by shutil.disk_usage
                'pct': {'reserve': DriveManager.reserve_pct, 'usable': DriveManager.usable_pct, 'warning': DriveManager.warning_pct},
                'actual_capacity': actual_capacity, # available bytes to use after reserve is taken into account
                'actual_pct_used': actual_pct_used,
                'actual_pct_used_warning': actual_pct_used >= DriveManager.warning_pct,
                'actual_pct_used_breach': actual_pct_used >= 1,
                'harvest_needed': actual_pct_used >= 1,
                'session_basenames': session_basenames,
                'available_bytes_gb': -1,
                'has_free_space': None,
                'min_session_id': min_session_id,
                'max_session_id': max_session_id,
                }

            available_bytes_gb, has_free_space = cls.get_free_space(drive_info,n_workstations=10)
            drive_info['available_bytes_gb'] = available_bytes_gb
            drive_info['has_free_space'] = has_free_space

            video_storage.append(drive_info)

        return video_storage
        # usable_free_space = hdd_1.total - (hdd_1.total * g.storage['reserve'])
        # video_storage = [{'drive': drive,'active': drive == self.cur_drive, 'stats': shutil.disk_usage(drive)} \
        #     for drive in g.paths['hdd']]

    @classmethod
    def calc_chapter_stats(cls,wsid,chapters):
        """Compute chapter_stats for all chapters for this wsid

        Args:
            wsid (str): ex. "ws01", "ws02", etc
            chapters (list of str): list of abs paths to chapter files for `wsid`
                                    it is assumed "chapters" contains only chapters for this wsid
        Returns:
            [list of dict]: each dict is in depth info on corresponding chapter file

        """

        # TODO: Refactor this into it's own class
        chapter_stats = {
            'wsid_int' : utils.wsid2int(wsid),
            'wsid': wsid,
            'time': -1,
            'size': -1, # total_filesize combining all chapters for this wsid
            'chapters': chapters, # list of fullnames of all chapters with this wsid
            'min_chapter_id': 0,
            'max_chapter_id': 99999999,
            'chapter_count': len(chapters),
            'filestats': [], # one for each chapter file, last one is most recent
        }

        # Compute total size of the file by adding up size of all chapters for this wsid
        # TODO: Account for overlap portions when computing total filesize
        total_filesize = 0
        min_chapter_id = 99999999
        max_chapter_id = 0
        for fullname in chapters:
            wsid, chapter_id, dt = cls.parse_chapter_file_name(fullname)
            chapter_size = os.path.getsize(fullname)
            total_filesize += chapter_size # TODO: update for overlap
            if chapter_id < min_chapter_id:
                min_chapter_id = chapter_id
            if chapter_id > max_chapter_id:
                max_chapter_id = chapter_id
            chapter_stats['filestats'].append({
                'basename': os.path.basename(fullname),
                'fullname': fullname,
                'chapter_id': chapter_id,
                'chapter_size': chapter_size
            })
        chapter_stats['min_chapter_id'] = min_chapter_id
        chapter_stats['max_chapter_id'] = max_chapter_id
        chapter_stats['size'] = total_filesize

        return chapter_stats

    @classmethod
    def get_chapter_stats(cls,drive_dirs,session_dir,vid_ext='.mp4'):
        """Returns list of all chapter stats in the session_dir

        Args:
            drive_dirs (list[str]): list of drive paths
            session_dir (str): abs or basename of session directory
            vid_ext (str, optional): video file extension. Defaults to '.mp4'.

        Returns:
            list[dict]: each element is chapter_stats returned by calc_chapter_stats, 
                        one for each workstation. If the session_dir spans multiple drives
                        then it will return a chapter_stats for each workstation on each drive
        """

        all_chapter_stats = []

        if type(drive_dirs) != list:
            drive_dirs = [drive_dirs]

        # Build list of chapter files residing in session_dir on all drive_dirs
        filelist = []
        basedir = os.path.basename(session_dir)
        for drive in drive_dirs:
            hdd_dirpath = os.path.join(drive,basedir)
            if os.path.isdir(hdd_dirpath): # session dir might not span over multiple drives yet so ignore the drive if dne
                hdd_filelist = os.listdir(hdd_dirpath)
                for i,f in enumerate(hdd_filelist):
                    absf = os.path.join(hdd_dirpath,f)
                    if os.path.isfile(absf) and len(absf) > len(vid_ext) and absf[-4:] == vid_ext: # make sure we skip any non .mp4 files and dirs
                        filelist.append(absf)
        filelist.sort()

        # iterate over filelist breaking them into chapter slices by workstation as you move along
        si = 0
        cur_wsid = None
        for i,f in enumerate(filelist):
            last_file = (i == len(filelist)-1)
            wsid, chunk_id , dt = cls.parse_chapter_file_name(f)
            if i == 0:
                cur_wsid = wsid
            if cur_wsid != wsid:
                filelist_slice = filelist[si:i]
                chapter_stats = cls.calc_chapter_stats(cur_wsid,filelist_slice)
                all_chapter_stats.append(chapter_stats)
                si = i
                cur_wsid = wsid
            if last_file:
                filelist_slice = filelist[si:]
                chapter_stats = cls.calc_chapter_stats(cur_wsid,filelist_slice)
                all_chapter_stats.append(chapter_stats)

        return all_chapter_stats

    @classmethod
    def get_next_drive2(cls,active_drive,drive_stats):
        """Returns next drive to use after `active_drive`.

        Args:
            active_drive (str): abs path to current active drive
            drive_stats (list[dict]): drive stats of all drives returned by get_video_storage_stats

        Returns:
            dict: drive stats of next drive to start recording on
        """
        ndrives = len(drive_stats)
        idx, dstat = cls.find_drive_stat(active_drive,drive_stats)
        return drive_stats[(idx+1)%ndrives] if (not idx == None) and idx >= 0 else None
    
    @classmethod
    def find_drive_stat(cls,drive_name,drive_stats):
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
            if d['drive'] == drive_name:
                dstat = d
                idx = i
                break
        return idx, dstat

    @classmethod
    def get_chapters_in_session(cls,session_basename,drive_dirs=g.paths['hdd']):
        ''' Returns list of ALL chapters in 'session_basename' spanning all drives sorted by creation time
        '''

        chapter_list = []
        for i,drive_dir in enumerate(drive_dirs):

            # Build list of chapter files (fullpaths) in session_dir on drive_dir
            session_path = os.path.join(drive_dir,session_basename)
            file_list = os.listdir(session_path)
            file_paths = []
            for file in file_list:
                path = os.path.join(session_path,file)
                if os.path.isdir(path): # skip over sdp directory
                    continue
                file_paths.append(path)

            # Sort them by creation time and returned as list of tuples (creation_time, file_path)
            clist = utils.sort_files_by_creation_time(file_paths) # returns list of sorted (creation_time, file_path) tuples
            chapter_list.extend(clist)

        chapter_list.sort()
        return chapter_list

    @classmethod
    def find_drive_by_chapter(cls,drive_dirs,session_dir,criteria='newest'):
        ''' Returns the drive containing either the "oldest" or "newest" chapter files by creation_time

            Note that chapter_list is a list of ALL chapters in session_dir spanning "drive_dirs"
        '''
        chosen_drive = None
        chapter_list = []
        stored_creation_time = None
        for i,drive_dir in enumerate(drive_dirs):
            
            print(f'i: {i}')

            # Build list of chapter files (fullpaths) in session_dir on drive_dir
            session_path = os.path.join(drive_dir,session_dir)
            if not os.path.isdir(session_path):
                print(f'session_path: {session_path}')
                print(f'1st continue: {i}')
                continue
            file_list = os.listdir(session_path)
            file_paths = []
            for file in file_list:
                path = os.path.join(session_path,file)
                if os.path.isdir(path): # skip over sdp
                    print(f'2nd continue: {i}')
                    continue
                file_paths.append(path)

            # Sort them by creation time and returned as list of tuples (creation_time, file_path)
            clist = utils.sort_files_by_creation_time(file_paths) # returns list of sorted (creation_time, file_path) tuples
            # TODO: Investigate potential bugs here when session directories exist without files in them
            if not clist:
                print(f'3rd continue: {i}')
                continue

            print(f'i: {i} -- stored_creation_time: {stored_creation_time}')
            # Add clist to giant chapter_list (all chapters spanning drive_dirs in session_dir)
            # if i == 0: # if first drive
            if not stored_creation_time:
                if criteria == 'oldest':
                    stored_creation_time = clist[0][0]
                elif criteria == 'newest':
                    stored_creation_time = clist[-1][0]
                chosen_drive = drive_dir
                chapter_list.extend(clist)
            else:
                if criteria == 'oldest' and clist[0][0] < stored_creation_time:
                    chosen_drive = drive_dir
                elif criteria == 'newest' and clist[-1][0] > stored_creation_time:
                    chosen_drive = drive_dir
                chapter_list.extend(clist)

        chapter_list.sort()
        return chosen_drive, chapter_list

    @classmethod
    def pick_best_drive2(cls,active_drive,n_workstations):
        ''' Returns the best drive to start the next recording session on, also returns the last session id '''

        # logger.debug('--------------------------------DriveManager.pick_best_drive2()------------------------------------')
        # logger.debug(f'Active Drive: {active_drive}')

        chosen_drive = None

        # Get current drive snapshot
        drive_stats = cls.get_video_storage_stats(active_drive=active_drive)
        for drive in drive_stats:
            if drive['active']:
                active_drive_stat = drive

        drives = g.paths['hdd']
        _, _, max_session_id = get_all_sessions(drives)

        if max_session_id == 0:
            logger.debug('=================================================')
            logger.debug('NO SESSIONS STORED ON ANY DRIVES')
            logger.debug('Selecting "defaultSaveLocation" defined in dcp_config.txt')
            logger.debug('=================================================')
            return g.paths['viddir'], max_session_id

        if active_drive_stat['has_free_space']:
            logger.debug('ACTIVE DRIVE HAS FREE SPACE')
            chosen_drive = active_drive_stat['drive']
        else:
            next_drive = cls.get_next_drive2(active_drive,drive_stats)
            if not next_drive['has_free_space']:
                logger.debug('NO FREE SPACE -- FREEING UP SPACE')
                chosen_drive = cls.make_free_space(active_drive,n_workstations)
            else:
                logger.debug('NEXT DRIVE HAS FREE SPACE')
                chosen_drive = next_drive['drive']
        logger.debug(f'chosen_drive -- {chosen_drive}')
        return chosen_drive, max_session_id

    #--------------------------------------------------------------------------------------
    #--------------------------------------------------------------------------------------
    #--------------------------------------------------------------------------------------
    
    @classmethod
    def __drive_stat_to_string(cls,drive_info):
        drive_basename = os.path.basename(drive_info['drive'])
        stats = drive_info['stats']
        reserve_pct = f'{(DriveManager.reserve_pct*100):.2f}'
        actual_capacity_gb = f'{utils.bytesto(drive_info["actual_capacity"],"gb"):.2f}'
        actual_pct_used = f'{drive_info["actual_pct_used"]*100:.2f}'
        actual_free_gb = f'{drive_info["available_bytes_gb"]:.2f}'
        capacity_status = f'(warn,breach,harvest): {drive_info["actual_pct_used_warning"],drive_info["actual_pct_used_breach"],drive_info["harvest_needed"]}'

        # this doesn't work in unit test for some reason, I think it's process related bullshit
        is_active = '(ACTIVE)' if drive_info['active'] == True else '        '

        output = \
f'''
--------------------------------------------------------------------------------------
({actual_pct_used}%)
{drive_basename}: free {utils.bytesto(stats.free,"gb"):.2f} GB / used {utils.bytesto(stats.used,"gb"):.2f} GB / total {utils.bytesto(stats.total,"gb"):.2f} GB / {threading.current_thread().name}
     actual: ({actual_pct_used}%) / free_gb {actual_free_gb} GB / total {actual_capacity_gb} GB / reserve {reserve_pct}% / has_free_space: {drive_info["has_free_space"]}
     warning at {drive_info["pct"]["warning"]*100}% / {capacity_status}
     max_session_id: {drive_info["max_session_id"]} / sessions: {drive_info["session_basenames"]}
'''
        for session_basename in drive_info["session_basenames"]:
            output = f'{output}\n     {session_basename}'
            chapter_stats = DriveManager.get_chapter_stats(drive_info['drive'],session_basename)
            for chapter_stat in chapter_stats:
                output = f'{output}\n{cls.__chapter_stat_to_string_short2(chapter_stat,indent=8)}'

        return output

    @classmethod
    def print_drive_stat(cls,drive_info):
        print(cls.__drive_stat_to_string(drive_info))

    @classmethod
    def print_drive_stats(cls,drive_info):
        if type(drive_info) == list:
            for d in drive_info:
                cls.print_drive_stat(d)
        else:
            cls.print_drive_stat(drive_info)
    
    @classmethod
    def __chapter_stat_to_string_short(cls,chapter_stat,indent=0):
        # chapter_stats = {
        #     'wsid_int' : utils.wsid2int(wsid),
        #     'wsid': wsid,
        #     'time': -1,
        #     'size': -1, # total_filesize combining all chapters for this wsid
        #     'chapters': chapters, # list of fullnames of all chapters with this wsid
        #     'min_chapter_id': 0,
        #     'max_chapter_id': 99999999,
        #     'chapter_count': len(chapters),
        #     'filestats': [], # one for each chapter file, last one is most recent
        # }
        # chapter_stats['filestats'].append({
        #         'basename': os.path.basename(fullname),
        #         'fullname': fullname,
        #         'chapter_id': chapter_id,
        #         'chapter_size': chapter_size
        #     })
        wsid  = chapter_stat['wsid']
        idmin = chapter_stat['min_chapter_id']
        idmax = chapter_stat['max_chapter_id']
        cnt   = chapter_stat['chapter_count']
        spaces = indent * ' '
        output = \
f'''{spaces}{wsid} | (min,max,cnt) ({idmin},{idmax},{cnt}) |'''
        return output

    @classmethod
    def __build_chapter_range_str(cls,chapter_stat):
        '''Returns string representing chapter_stat['filestats'] chapter_id's as a group of ranges
        
        Example: [0,1,2,4,6,7,8,12,13,14,15,16] would return "[0-2] [4-4] [6-8] [12-16]"
        Note: Assumes chapter_stat['filestats'] is sorted by id
        '''
        range_str = ''

        # filestats is a list dicts containing info about each chapter file
        filestats = chapter_stat['filestats']
        if not filestats: return range_str

        start_id = end_id = prev_id = filestats[0]['chapter_id']
        for x in range(1,len(filestats)):
            chapter_id = filestats[x]['chapter_id']
            if ((chapter_id-1) != prev_id):
                # we have located a new block of ids
                end_id = prev_id
                range_str = f'{range_str} [{start_id}-{end_id}]'
                start_id = chapter_id
            prev_id = chapter_id
        end_id = filestats[-1]['chapter_id']
        range_str = f'{range_str} [{start_id}-{end_id}]'
        return range_str

    # @classmethod
    # def __build_chapter_range_str(id_list):
    #     '''Returns string representing id_list as a group of ranges
    #     Example: [0,1,2,4,6,7,8,12,13,14,15,16] would return "[0-2] [4-4] [6-8] [12-16]"
    #     '''
    #     range_str = ''
    #     if not id_list: return range_str

    #     start_id = end_id = prev_id = id_list[0]
    #     for x in range(1,len(id_list)):
    #         chapter_id = id_list[x]
    #         if ((chapter_id-1) != prev_id):
    #             # we have located a new block of ids
    #             end_id = prev_id
    #             range_str = f'{range_str} [{start_id}-{end_id}]'
    #             start_id = chapter_id
    #         prev_id = chapter_id
    #     end_id = id_list[-1]
    #     range_str = f'{range_str} [{start_id}-{end_id}]'
    #     return range_str

    @classmethod
    def __chapter_stat_to_string_short2(cls,chapter_stat,indent=0):
        wsid  = chapter_stat['wsid']
        idmin = chapter_stat['min_chapter_id']
        idmax = chapter_stat['max_chapter_id']
        cnt   = chapter_stat['chapter_count']
        spaces = indent * ' '
        range_str = cls.__build_chapter_range_str(chapter_stat)
        output = \
f'''{spaces}{wsid} | (min,max,cnt) ({idmin},{idmax},{cnt}) | {range_str}'''
        return output

    @classmethod
    def __chapter_stat_to_string_long(cls,chapter_stat,indent=0):
        spaces = indent * ' '
        output = \
f'''{spaces}--------------------------------------------------------------------------------------
{spaces}wsid: {chapter_stat['wsid']}
{spaces}min_chapter_id: {chapter_stat['min_chapter_id']}, max_chapter_id: {chapter_stat['max_chapter_id']}
{spaces}chapter_count: {chapter_stat['chapter_count']}'''
        return output


    @classmethod
    def print_chapter_stat(cls,chapter_stat,desc='long',indent=0):
        if desc == 'short':
            print(cls.__chapter_stat_to_string_short(chapter_stat,indent))
        elif desc == 'short2':
            print(cls.__chapter_stat_to_string_short2(chapter_stat,indent))
        elif desc == 'long':
            print(cls.__chapter_stat_to_string_long(chapter_stat,indent))

    @classmethod
    def print_chapter_stats(cls,chapter_stats,desc='long',indent=0):
        if type(chapter_stats) == list:
            for chapter_stat in chapter_stats:
                cls.print_chapter_stat(chapter_stat,desc,indent)
        else:
            cls.print_chapter_stat(chapter_stats,desc,indent)
    
    @classmethod
    def testlog(cls):
        logger.debug('Does this work??????')