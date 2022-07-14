import os
import sys

# TODO: this needs to not be hardcoded. Needs to work on RHEL7 as well
if not 'DCP_HOME' in os.environ:
    os.environ['DCP_HOME'] = '/home/cholland/devrepo/dcp/vidrecorder'
    sys.path.append(os.environ['DCP_HOME'])

import unittest

from global_vars import g
from components.drive import get_video_storage_stats
from components.drive import find_drive_stat
from components.drive import get_next_drive2
# from components.drive import delete_oldest_files
from components.drive import print_drive_stats


class TestSession(unittest.TestCase):

    def setUp(self):
        pass
    def tearDown(self):
        pass

    #------------------------------------------------------------------------------------------------
    # @unittest.skip("because I said so")
    def test_b1_get_video_storage_stats(self):
        print('\n================================================================================================')
        print('[ Testing b1: drive.get_video_storage_stats ]')
        # active_drive = '/mnt/dd1'
        from_drives = g.paths['hdd']
        active_drive = g.paths['hdd'][0] # dd1
        drive_stats = get_video_storage_stats(from_drives,active_drive)
        print_drive_stats(drive_stats)

    #------------------------------------------------------------------------------------------------
    # @unittest.skip("because I said so")
    def test_b2_find_drive_stat(self):
        print('\n================================================================================================')
        print('[ Testing b2: drive.find_drive_stat ]')

        from_drives = g.paths['hdd']
        active_drive = g.paths['hdd'][0] # dd1
        drive_stats = get_video_storage_stats(from_drives,active_drive)

        # drive = '/mnt/dd1'
        drive = from_drives[0] # dd1
        idx, drive_stat = find_drive_stat(drive,drive_stats)
        self.assertEqual(drive,drive_stat.drivepath)
        self.assertEqual(idx,0)

        # drive = '/mnt/dd2'
        drive = from_drives[1] # dd2
        idx, drive_stat = find_drive_stat(drive,drive_stats)
        self.assertEqual(drive,drive_stat.drivepath)
        self.assertEqual(idx,1)

    #------------------------------------------------------------------------------------------------
    # @unittest.skip("because I said so")
    def test_b3_get_next_drive2(self):
        print('\n================================================================================================')
        print('[ Testing b3: drive.get_next_drive2 ]')

        from_drives = g.paths['hdd']

        active_drive = from_drives[0] # dd1
        expected_next_drive = from_drives[1]
        drive_stats = get_video_storage_stats(from_drives,active_drive)
        next_drive = get_next_drive2(active_drive,drive_stats)
        print(f'active_drive: {active_drive} -- next_drive: {next_drive.drivepath if next_drive else "None"}')
        self.assertEqual(expected_next_drive,next_drive.drivepath)

        active_drive = from_drives[1] # dd2
        expected_next_drive = from_drives[0]
        drive_stats = get_video_storage_stats(from_drives,active_drive)
        next_drive = get_next_drive2(active_drive,drive_stats)
        print(f'active_drive: {active_drive} -- next_drive: {next_drive.drivepath if next_drive else "None"}')
        self.assertEqual(expected_next_drive,next_drive.drivepath)

        active_drive = '/mnt/dd3' # drive that doesn't exist
        drive_stats = get_video_storage_stats(from_drives,active_drive)
        next_drive = get_next_drive2(active_drive,drive_stats)
        print(f'active_drive: {active_drive} -- next_drive: {next_drive["drive"] if next_drive else "None"}')
        self.assertIsNone(next_drive)

    # QUESTION FOR AFTER VACATION:
    # Do we want to include delete_oldest_files (and other related DriveManager funcs) in the drive.py module?
    #
    # @unittest.skip("don't run this unless you comment on delete portions of code")
    # def test_b4_delete_oldest_files(self):
    #     print('\n================================================================================================')
    #     print('[ Testing b4: drive.delete_oldest_files ]')

    #     n_workstations = 3
    #     delete_oldest_files(n_workstations)

if __name__ == '__main__':
    unittest.main()