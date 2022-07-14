import os
import sys
import threading

# TODO: this needs to not be hardcoded. Needs to work on RHEL7 as well
if not 'DCP_HOME' in os.environ:
    os.environ['DCP_HOME'] = '/home/cholland/devrepo/dcp/vidrecorder'
    sys.path.append(os.environ['DCP_HOME'])

import unittest

from global_vars import g
from DriveManager import DriveManager
from DeviceRecorder import DeviceRecorder
from utils.utils import isempty

from components.session import Session
from components.session import get_all_sessions


class TestDriveManager(unittest.TestCase):

    def setUp(self):
        pass
    def tearDown(self):
        pass

#------------------------------------------------------------------------------------------------
    @unittest.skip("because I said so")
    def test_b1_parse_chapter_file_name(self):
        print('\n================================================================================================')
        print('[ Testing: DriveManager.parse_chapter_file_name ]')
        test_filelist = [
            'ws04_0066_0.mp4','ws01_9999_2.1.mp4','ws10_0000_3.3.mp4'
        ]
        for f in test_filelist:
            print(type(DriveManager.parse_chapter_file_name(f)))
#         for f in test_filelist:
#             wsid, chaptid, dt = DriveManager.parse_chapter_file_name(f)
#             output = f'''
# wsid: {wsid} ({type(wsid)}) -- chaptid: {chaptid} ({type(chaptid)}) -- dt: {dt} ({type(dt)})'''
#             print(output)


#------------------------------------------------------------------------------------------------
    # @unittest.skip("because I said so")
    def test_b2_get_chapter_stats(self):
        print('\n================================================================================================')
        print('[ Testing b2: DriveManager.get_chapter_stats ]')
        drives = g.paths['hdd']
        sessions, min_session_id, max_session_id = get_all_sessions(drives)
        print(f'min_session_id: {min_session_id}, max_session_id: {max_session_id}')
        for sess in sessions:
            print(sess._str_oneline(indent=3))
            session_dir = sess.basename
            chapter_stats = DriveManager.get_chapter_stats(drives,session_dir,vid_ext='.mp4')
            DriveManager.print_chapter_stats(chapter_stats,desc='short',indent=6)



#------------------------------------------------------------------------------------------------
    # @unittest.skip("because I said so")
    def test_b3_find_drive_by_chapter(self):
        print('\n================================================================================================')
        print('[ Testing b3: DriveManager.find_drive_by_chapter ]')
        drives = g.paths['hdd']
        sessions, min_session_id, max_session_id = get_all_sessions(drives)
        if not sessions:
            print('No sessions on drives')
            return

        print(f'min_session_id: {min_session_id}, max_session_id: {max_session_id}')
        for sess in sessions:
           print(sess._str_oneline(indent=3))
        oldest_session_basename = sessions[0].basename
        newest_session_basename = sessions[-1].basename
        print(f'oldest session basename: {oldest_session_basename}')
        print(f'newest session basename: {newest_session_basename}')

        chosen_drive, chapter_list = \
            DriveManager.find_drive_by_chapter(drives,newest_session_basename,'oldest')

        n_files_to_delete = 2
        print(chosen_drive)
        for tpl in chapter_list:
            p = tpl[1]
            print(f' >>>>>>>>> File : {tpl}')



#------------------------------------------------------------------------------------------------
    @unittest.skip("because I said so")
    def test_get_free_space(self):
        # cur_drive = '/mnt/dd1'
        cur_drive = g.paths['hdd'][0] # dd1
        drive_stats = DriveManager.get_video_storage_stats(active_drive=cur_drive)
        # Testing: DriveManager.get_free_space(cls,drive_stats,n_workstations)
        print('\n================================================================================================')
        print('[ Testing: DriveManager.get_free_space ]')
        for drive_stat in drive_stats:
            bytes_available_gb, has_free_space = DriveManager.get_free_space(drive_stat,0)
            used_pct = drive_stat["actual_pct_used"]
            print(f'(%{used_pct*100:.2f}) drive: {drive_stat["drive"]} -- bytes_available_gb: {bytes_available_gb} -- has_free_space: {has_free_space}')



#------------------------------------------------------------------------------------------------
    @unittest.skip("because I said so")
    def test_y_video_storage_stats(self):
        print('\n================================================================================================')
        print('[ Testing: DriveManager.get_video_storage_stats ]')
        # active_drive = '/mnt/dd1'
        active_drive = g.paths['hdd'][0] # dd1
        drive_stats = DriveManager.get_video_storage_stats(active_drive=active_drive)
        DriveManager.print_drive_stats(drive_stats)



#------------------------------------------------------------------------------------------------
    # @unittest.skip("because I said so")
    def test_z5_overall_report(self):
        print('\n================================================================================================')
        print(f'[ OVERALL REPORT ] -- {threading.current_thread().name}')
        active_drive = g.paths['viddir'] # DeviceRecorder.best_drive doesn't work. Process issue I think
        drive_stats = DriveManager.get_video_storage_stats(active_drive=active_drive)
        DriveManager.print_drive_stats(drive_stats)


#------------------------------------------------------------------------------------------------
    @unittest.skip("because I said so")
    def test_z1_find_drive_stat(self):
        print('\n================================================================================================')
        print('[ Testing: DriveManager.find_drive_stat ]')

        active_drive = g.paths['viddir'] # DeviceRecorder.best_drive doesn't work. Process issue I think
        drive_stats = DriveManager.get_video_storage_stats(active_drive=active_drive)

        # drive = '/mnt/dd1'
        drive = g.paths['hdd'][0] # dd1
        idx, dstat = DriveManager.find_drive_stat(drive,drive_stats)
        self.assertEqual(drive,dstat['drive'])
        self.assertEqual(idx,0)

        # drive = '/mnt/dd2'
        drive = g.paths['hdd'][1] # dd2
        idx, dstat = DriveManager.find_drive_stat(drive,drive_stats)
        self.assertEqual(drive,dstat['drive'])
        self.assertEqual(idx,1)
        
#------------------------------------------------------------------------------------------------
    @unittest.skip("because I said so")
    def test_z2_get_next_drive2(self):
        print('\n================================================================================================')
        print('[ Testing: DriveManager.get_next_drive2 ]')

        # active_drive = '/mnt/dd1'
        active_drive = g.paths['hdd'][0] # dd1
        drive_stats = DriveManager.get_video_storage_stats(active_drive=active_drive)
        next_drive = DriveManager.get_next_drive2(active_drive,drive_stats)
        print(f'active_drive: {active_drive} -- next_drive: {next_drive["drive"] if next_drive else "None"}')
        self.assertEqual("/mnt/dd2",next_drive["drive"])

        # active_drive = '/mnt/dd2'
        active_drive = g.paths['hdd'][1] # dd2
        drive_stats = DriveManager.get_video_storage_stats(active_drive=active_drive)
        next_drive = DriveManager.get_next_drive2(active_drive,drive_stats)
        print(f'active_drive: {active_drive} -- next_drive: {next_drive["drive"] if next_drive else "None"}')
        self.assertEqual("/mnt/dd1",next_drive["drive"])
        
        active_drive = '/mnt/dd3' # drive that doesn't exist
        drive_stats = DriveManager.get_video_storage_stats(active_drive=active_drive)
        next_drive = DriveManager.get_next_drive2(active_drive,drive_stats)
        print(f'active_drive: {active_drive} -- next_drive: {next_drive["drive"] if next_drive else "None"}')
        self.assertIsNone(next_drive)

#------------------------------------------------------------------------------------------------
    @unittest.skip("don't run this unless you comment on delete portions of code")
    def test_z3_delete_oldest_files(self):
        print('\n================================================================================================')
        print('[ Testing: DriveManager.delete_oldest_files ]')

        n_workstations = 3
        DriveManager.delete_oldest_files(n_workstations)

#------------------------------------------------------------------------------------------------
    @unittest.skip("don't run this unless you comment on delete portions of code")
    def test_z4_make_free_space(self):
        print('\n================================================================================================')
        print('[ Testing: DriveManager.make_free_space ]')

        # active_drive = '/mnt/dd2'
        active_drive = g.paths['hdd'][1]
        n_workstations = 3
        chosen_drive = DriveManager.make_free_space(active_drive,n_workstations)
        print(f'chosen_drive: {chosen_drive}')
        
#------------------------------------------------------------------------------------------------
    @unittest.skip("don't run this unless you comment on delete portions of code")
    def test_z6_pick_best_drive(self):
        print('\n================================================================================================')
        print('[ Testing: DriveManager.pick_best_drive ]')

       # active_drive = '/mnt/dd2'
        active_drive = g.paths['hdd'][1] # dd2
        n_workstations = 3
        chosen_drive = DriveManager.pick_best_drive2(active_drive,n_workstations)
        print(f'chosen_drive: {chosen_drive}')


if __name__ == '__main__':
    unittest.main()