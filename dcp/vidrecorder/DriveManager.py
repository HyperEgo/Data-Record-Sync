import os
import threading
import shutil

from global_vars import g
from utils import utils
import utils.vidlogging as vidlogging

logger = vidlogging.get_logger(__name__,filename=g.paths['logfile'])

class DriveManager():
    
    @classmethod
    def parse_chapter_file_name(self,filename):
        '''parse format <wsid>_<chunkid>_<dt>.mp4 into it's components, abs or rel paths ok'''
        wsid = None; chunkid = None; dt = None
        if filename:
            basename = os.path.basename(filename)
            parts = basename.split('_')
            if len(parts) == 1: # old filename format <wsid>.mp4
                s = parts[0].split('.')
                wsid = s[0]
            elif len(parts) == 3: # new filename format <wsid>_<chunkid>_<dt>.mp4
                wsid = parts[0]
                chunkid = int(parts[1])
                dt = float(parts[2][0:parts[2].rfind('.')])
        return wsid, chunkid, dt
    
    @classmethod
    def print_drive_stat(cls,drive_info):
        drive_basename = os.path.basename(drive_info['drive'])
        stats = drive_info['stats']
        print('--------------------------------------------------------------------------------------')
        print(f'{drive_basename}: free {utils.bytesto(stats.free,"gb"):.2f} GB / used {utils.bytesto(stats.used,"gb"):.2f} GB / total {utils.bytesto(stats.total,"gb"):.2f} GB / {threading.current_thread().name} \n' \
              f'     actual_capacity: {utils.bytesto(drive_info["actual_capacity"],"gb"):.2f} GB / ' \
              f'actual_pct_used: {drive_info["actual_pct_used"]*100:.2f}% / warning at {drive_info["pct"]["warning"]*100}% / ' \
              f'(warn,breach,harvest): {drive_info["actual_pct_used_warning"],drive_info["actual_pct_used_breach"],drive_info["harvest_needed"]} / \n' \
              f'     max_session_id: {drive_info["max_session_id"]}, sessions: {drive_info["session_basenames"]}')

    @classmethod
    def print_drive_stats(cls,drive_info):
        if type(drive_info) == list:
            for d in drive_info:
                cls.print_drive_stat(d)
        else:
            cls.print_drive_stat(drive_info)
            

    @classmethod
    def print_chapter_stat(cls,chapter_stat):
        print('--------------------------------------------------------------------------------------')
        print(f'''wsid: {chapter_stat['wsid']}
min_chapter_id: {chapter_stat['min_chapter_id']}, max_chapter_id: {chapter_stat['max_chapter_id']}
chapter_count: {chapter_stat['chapter_count']}
              ''')
        chapters = chapter_stat['chapters']
        for c in chapters:
            print(c)
        # filestats = {
        #     'wsid': wsid,
        #     'time': -1,
        #     'size': -1, # total_filesize combining all chapters for this wsid
        #     'basename': '', # this will be basename of last chapter file
        #     'fullname': '', # this will be fullname of last chapter file
        #     'chapter_size': -1, # this will be filesize of last chapter file
        #     'chapters': chapters, # list of fullnames of all chapters with this wsid
        #     'min_chapter_id': 0,
        #     'max_chapter_id': 99999999,
        #     'chunk_count': len(chapters), # TODO: remove this when you get a chance to refactor
        #     'chapter_count': len(chapters),
        # }
    @classmethod
    def print_chapter_stats(cls,chapter_stats):
        if type(chapter_stats) == list:
            for chapter_stat in chapter_stats:
                cls.print_chapter_stat(chapter_stat)
        else:
            cls.print_chapter_stat(chapter_stats)

    @classmethod
    def get_free_space(cls,drive_stat,n_workstations):

        actual_capacity = drive_stat['actual_capacity']
        actual_pct_used = drive_stat['actual_pct_used']

        bytes_available = actual_capacity * (1-actual_pct_used)
        bytes_available_gb = utils.bytesto(bytes_available,'gb')

        has_free_space = not drive_stat['actual_pct_used_breach']

        return bytes_available_gb, has_free_space
    
    @classmethod
    def make_free_space(cls,drive_stat,n_chapter_blocks,n_workstations,from_session_id,chapter_list=None):
        '''Free up "n_chapter_blocks" of space on this drive

           Algorithm:
           Case 1: if no sessions --> return do nothing
           Case 2: if multiple sessions --> delete oldest sessions until enough space has been released 
           Case 3: if one session -->
                     delete "n_chapter_blocks" worth of files in the session
        '''

        drive = drive_stat['drive']
        sessions = drive_stat['session_basenames']
        sessions.sort()
        
        # Case 1: if no sessions --> return do nothing
        if not sessions: 
            return

        # Case 2: if multiple sessions --> delete oldest sessions until enough space has been released 
        if len(sessions) > 1:
            delete_list = []
            total_files_to_delete = n_chapter_blocks*n_workstations
            for i in range(len(sessions)-1):
                session_dir_to_delete = os.path.join(drive,sessions[i])
                print(f'drive: {drive} -- session_dir_to_delete: {session_dir_to_delete}')
                delete_list.append(session_dir_to_delete)
                ws_chapter_stats = cls.get_chapter_stats(drive,session_dir_to_delete,vid_ext='.mp4')
                cls.print_chapter_stats(ws_chapter_stats)
                total_chapter_count = 0
                for ws_chapter_stat in ws_chapter_stats:
                    total_chapter_count += ws_chapter_stat['chapter_count']
                if total_chapter_count >= total_files_to_delete:
                    break
                else:
                    total_files_to_delete -= total_chapter_count
                print(f'total_files_to_delete: {total_files_to_delete} -- {total_chapter_count}')
                    
            print(f'delete_list: {delete_list}')
            for directory in delete_list:
                shutil.rmtree(directory)
            
        else: # only one session
            # Case 3: if one session -->
            #         delete "n_chapter_blocks" worth of files in the session
            
            one_session_id = drive_stat['max_session_id']
            if (from_session_id != one_session_id):
                session_dir = os.path.join(drive,sessions[0])
                shutil.rmtree(session_dir)
            else: 
                # drive_dirs = g.paths['hdd']
                session_dir = os.path.join(drive,sessions[0])
                if not chapter_list:
                    chosen_drive, chapter_list = cls.find_drive_by_chapter([drive],session_dir,'oldest')
                
                # delete oldest chapter sets on this drive
                n_files_to_delete = n_chapter_blocks * n_workstations
                logger.info(f'n_files_to_delete: {n_files_to_delete}')
                for tpl in chapter_list[0:n_files_to_delete]:
                    p = tpl[1]
                    logger.info(f' >>>>>>>>> Deleting File : {tpl}')
                    p.unlink()
                # session_dir = os.path.join(drive,sessions[0])
                # chapter_stats = cls.get_chapter_stats(drive,session_dir)
                # for ws_chapter_stat in chapter_stats:
                #     chapters = ws_chapter_stat['chapters']
                #     delete_chapters = chapters[:n_chapter_blocks]
                #     for absf in delete_chapters:
                #         # TODO: Delete files when ready
                #         print(f'chapter to be deleted: {absf}')
                #         os.remove(absf)

    @classmethod
    def get_video_storage_stats(cls,active_drive,from_drives=g.paths['hdd']):

        video_storage = []
        reserve_pct = g.storage['reserve']
        usable_pct  = 1-g.storage['reserve']
        warning_pct = 0.7
        
        if type(from_drives) != list:
            from_drives = [from_drives]
        hdd = from_drives
        for drive in hdd:
            drive_stats = shutil.disk_usage(drive)
            actual_capacity = drive_stats.total * usable_pct
            actual_pct_used = drive_stats.used/actual_capacity
            session_basenames, min_session_id, max_session_id = cls.get_session_stats(drive)

            drive_info = {
                'drive': drive, # path to drive
                'active': drive == active_drive, # is this the drive currently being written to?
                'stats': drive_stats, # as returned by shutil.disk_usage
                'pct': {'reserve': reserve_pct, 'usable': usable_pct, 'warning': warning_pct},
                'actual_capacity': actual_capacity, # available bytes to use after reserve is taken into account
                'actual_pct_used': actual_pct_used,
                'actual_pct_used_warning': actual_pct_used >= warning_pct,
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
    def get_session_stats(cls,drive):
        ''' Returns all session basenames in the drive, and the max session id on this drive '''
        sessions = []
        min_session_id = 99999999
        max_session_id = 0
        file_list = os.listdir(drive)
        for f in file_list:
            if os.path.isdir(os.path.join(drive,f)):
                basename = f
                parts = basename.split('_')
                session_id = utils.str2int(parts[0])
                if session_id == None:
                    continue
                if session_id > max_session_id:
                    max_session_id = session_id
                if session_id < min_session_id:
                    min_session_id = session_id
                sessions.append(basename)
        sessions.sort()

        return sessions, min_session_id, max_session_id
    
    @classmethod
    def calc_chapter_stats(cls,wsid,chapters):
        '''Compute filestats for all chapters for this wsid

           it is assumed "chapters" contains only chapters for this wsid
        '''
        filestats = {
            'wsid': wsid,
            'time': -1,
            'size': -1, # total_filesize combining all chapters for this wsid
            'basename': '', # this will be basename of last chapter file
            'fullname': '', # this will be fullname of last chapter file
            'chapter_size': -1, # this will be filesize of last chapter file
            'chapters': chapters, # list of fullnames of all chapters with this wsid
            'min_chapter_id': 0,
            'max_chapter_id': 99999999,
            'chunk_count': len(chapters), # TODO: remove this when you get a chance to refactor
            'chapter_count': len(chapters),
        }
        # Compute total size of the file by adding up size of all chapters for this wsid
        total_filesize = 0
        min_chapter_id = 99999999
        max_chapter_id = 0
        for fullname in chapters:
            wsid, chapter_id, dt = cls.parse_chapter_file_name(fullname)
            total_filesize += os.path.getsize(fullname)
            if chapter_id < min_chapter_id:
                min_chapter_id = chapter_id
            if chapter_id > max_chapter_id:
                max_chapter_id = chapter_id
        filestats['min_chapter_id'] = min_chapter_id
        filestats['max_chapter_id'] = max_chapter_id
        filestats['size'] = total_filesize
        filestats['basename'] = os.path.basename(chapters[-1]) # this will be basename of last chapter file
        filestats['fullname'] = chapters[-1]
        filestats['chapter_size'] = os.path.getsize(chapters[-1])
        return filestats
    
    @classmethod
    def get_chapter_stats(cls,drive_dirs,session_dir,vid_ext='.mp4'):
        ''' Returns list of all chapter stats in the session_dir
        
            "drive_dirs" is a list of drive paths, caller gets to choose so be aware
        '''
        chapter_stats = []
        
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
                filestats = cls.calc_chapter_stats(cur_wsid,filelist_slice)
                chapter_stats.append(filestats)
                si = i
                cur_wsid = wsid
            if last_file:
                filelist_slice = filelist[si:]
                filestats = cls.calc_chapter_stats(cur_wsid,filelist_slice)
                chapter_stats.append(filestats)

        return chapter_stats

    @classmethod
    def get_next_drive(cls,from_idx,drive_stats):
        ndrives = len(drive_stats)
        return drive_stats[(from_idx+1)%ndrives]
    
    @classmethod
    def find_drive_by_chapter(cls,drive_dirs,session_dir,criteria='newest'):
        ''' Returns the drive and chapter_list containing either the "oldest" or "newest" chapter files by creation_time
        
            Note that chapter_list is a list of ALL chapters spanning "drive_dirs"
        '''
        chosen_drive = None
        chapter_list = []
        stored_creation_time = None
        for i,drive_dir in enumerate(drive_dirs):
            session_path = os.path.join(drive_dir,session_dir)
            file_list = os.listdir(session_path)
            file_paths = []
            for file in file_list:
                path = os.path.join(session_path,file)
                if os.path.isdir(path): # skip over sdp
                    continue
                file_paths.append(path)
            clist = utils.sort_files_by_creation_time(file_paths) # returns list of sorted (creation_time, file_path) tuples
            if i == 0: 
                if criteria == 'oldest':
                    stored_creation_time = clist[0][0]
                elif criteria == 'newest':
                    stored_creation_time = clist[-1][0]
                chosen_drive = drive_dir
                chapter_list.extend(clist)
            else:
                if criteria == 'oldest' and clist[0][0] < stored_creation_time:
                    chosen_drive = drive_dir
                    chapter_list.extend(clist)
                elif criteria == 'newest' and clist[-1][0] > stored_creation_time:
                    chosen_drive = drive_dir
                    chapter_list.extend(clist)

        chapter_list.sort()
        return chosen_drive, chapter_list

    @classmethod
    def pick_best_drive(cls,active_drive,n_workstations):
        ''' Returns the best drive to start the next recording session on, also returns the last session id '''

        # Determine which drive we will start recording on
        drive_stats = cls.get_video_storage_stats(active_drive)

        # Find the max_session_id on ALL the drives
        max_session_id = 0
        max_session_drive = drive_stats[0]
        max_session_drive_idx = 0
        for i,dstats in enumerate(drive_stats):
            if dstats['max_session_id'] > max_session_id:
                max_session_id = dstats['max_session_id']
                max_session_drive = dstats
                max_session_drive_idx = i

        if max_session_id == 0:
            print('=================================================')
            print('NO SESSIONS STORED ON EITHER DRIVE')
            print(f'max_session_id: {max_session_id} -- max_session_drive -- {max_session_drive["drive"]}')
            print('Selecting "defaultSaveLocation" defined in dcp_config.txt')
            print('=================================================')
            return g.paths['viddir'], max_session_id

        print('--------------------------------DriveManager.pick_best_drive()------------------------------------')
        chosen_drive = None

        # Does the most current session dir span all of the storage drives?
        for dstats in drive_stats:
            span = dstats['max_session_id'] == max_session_id
            if not span: break

        if not span:

            available_bytes_gb = max_session_drive['available_bytes_gb']
            has_free_space     = max_session_drive['has_free_space']
            print(f'has_free_space: {has_free_space} -- available_bytes_gb: {available_bytes_gb:.2f}')

            if has_free_space:
                # Case 1: don't span, free space on max_session_id drive
                #   - choose drive with max_session_id
                #   - try to start on drive
                print('=================================================')
                print(f'Case 1: NO SPAN -- free space on max_session_drive')
                print(f'max_session_id: {max_session_id} -- max_session_drive -- {max_session_drive["drive"]}')
                print('Selecting max_session_drive')
                print('=================================================')
                chosen_drive = max_session_drive['drive']
            else:
                # Case 2: don't span, no free space on max_session_id drive
                #   - check for oldest session on other drive and delete it if exists
                #   - choose next drive
                #   - try to start on drive
                # assume next is also full or empty
                print('=================================================')
                print(f'Case 2: NO SPAN -- no free space on max_session_id drive')
                print(f'max_session_id: {max_session_id} -- max_session_drive -- {max_session_drive["drive"]}')
                print('Selecting next drive and calling make_free_space')
                print('=================================================')
                next_drive = cls.get_next_drive(max_session_drive_idx,drive_stats)
                chosen_drive = next_drive['drive']
                if not next_drive['has_free_space']:
                    cls.make_free_space(next_drive,n_chapter_blocks=g.advanced['delete_chapters_per_ws'],n_workstations=n_workstations,from_session_id=max_session_id)
        else: # they span

            # has_free_space = [False for dstats in drive_stats]
            # for i,dstats in enumerate(drive_stats):
            #     has_free_space[i] = dstats['has_free_space']
            has_free_space = [dstats['has_free_space'] for dstats in drive_stats]

            if any(has_free_space):
                # Case 3: they do span
                #   - check each drive for free space, either one or both have free space available
                #   - check each for newest chapter file
                #   - choose this drive
                #   - try to start on drive
                drive_dirs = g.paths['hdd']
                session_dir = drive_stats[max_session_drive_idx]['session_basenames'][-1]
                if all(has_free_space):
                    print('=================================================')
                    print('Case 3a: SPAN -- all have free space')
                    print(f'max_session_id: {max_session_id} -- max_session_drive -- {max_session_drive["drive"]}')
                    print('Selecting drive with NEWEST chapter file set')
                    print('=================================================')
                    max_chapter_id = 0
                    for drive_dir in drive_dirs:
                        chapter_stats = cls.get_chapter_stats(drive_dir,session_dir,vid_ext='.mp4')
                        for i,chapter_stat in enumerate(chapter_stats):
                            if chapter_stat['max_chapter_id'] > max_chapter_id:
                                max_chapter_id = chapter_stat['max_chapter_id']
                                chosen_drive = drive_dir
                else:
                    print('=================================================')
                    print('Case 3b: SPAN -- just one free space')
                    print(f'max_session_id: {max_session_id} -- max_session_drive -- {max_session_drive["drive"]}')
                    print('Selecting the one drive with free space')

                    for i,free_space in enumerate(has_free_space):
                        if free_space == True:
                            chosen_drive = drive_stats[i]['drive']

                    print(f'has_free_space: {has_free_space} -- chosen_drive: {chosen_drive}')
                    print('=================================================')

            else:
                # Case 4: they do span
                #   - check each drive for free space, neither of them have free space
                #   - check each for oldest chapter file set
                #   - choose this drive
                #   - delete oldest chapter set on this drive
                #   - try to start on drive
                print('=================================================')
                print('Case 4: SPAN -- no free space on any drive')
                print(f'max_session_id: {max_session_id} -- max_session_drive -- {max_session_drive["drive"]}')
                print('Selecting drive with the OLDEST chapter creation times')
                drive_dirs = g.paths['hdd']
                session_dir = drive_stats[max_session_drive_idx]['session_basenames'][-1]
                chosen_drive, chapter_list = cls.find_drive_by_chapter(drive_dirs,session_dir,'oldest')
                
                for drive_stat in drive_stats:
                    if drive_stat['drive'] == chosen_drive:
                        cls.make_free_space(drive_stat,n_chapter_blocks=g.advanced['delete_chapters_per_ws'],n_workstations=n_workstations,from_session_id=max_session_id,chapter_list=chapter_list)

        return chosen_drive, max_session_id