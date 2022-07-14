import os
import sys
from datetime import datetime

# TODO: this needs to not be hardcoded. Needs to work on RHEL7 as well
if not 'DCP_HOME' in os.environ:
    os.environ['DCP_HOME'] = '/home/cholland/devrepo/dcp/vidrecorder'
    sys.path.append(os.environ['DCP_HOME'])

import unittest

from global_vars import g
from components.session import Session
from components.session import get_session_stats
from components.session import parse_session_dirpath
from components.session import find_session
from components.session import get_all_sessions

class TestSession(unittest.TestCase):

    def setUp(self):
        pass
    def tearDown(self):
        pass

    #------------------------------------------------------------------------------------------------
    # @unittest.skip("because I said so")
    def test_a1_get_session_stats(self):
        print('\n================================================================================================')
        print('[ Testing a1: session.get_session_stats ]')
        drives = g.paths['hdd']

        for drive in drives:
            session_basenames, min_session_id, max_session_id = get_session_stats(drive)
            print(f'drive: {drive}: min_session_id: {min_session_id}, max_session_id: {max_session_id}')
            for basename in session_basenames:
                print(f'   {basename}')

    #------------------------------------------------------------------------------------------------
    # @unittest.skip("because I said so")
    def test_a2_parse_session_dirpath(self):
        print('\n=============================================================================')
        print('[ Testing a2: session.parse_session_dirpath ]')

        session_list = [
            [Session("01_2022-Apr-11_05h50m32s"),1,'2022-Apr-11_05h50m32s'],
            [Session("02_2022-Apr-11_07h18m15s"),2,'2022-Apr-11_07h18m15s'],
            [Session("03_2022-Apr-11_07h20m12s"),3,'2022-Apr-11_07h20m12s'],
            [Session("04_2022-Apr-11_07h31m49s"),4,'2022-Apr-11_07h31m49s'],
            [Session("99_2021-Jul-24_01h59m59s"),99,'2021-Jul-24_01h59m59s'],
        ]

        for sess in session_list:
            sess_obj = sess[0]
            expected_id = sess[1]
            expected_date_str = sess[2]
            print(sess_obj._str_oneline(indent=3))
            self.assertEqual(sess_obj.id,expected_id)
            self.assertEqual(
                sess_obj.datetime,
                datetime.strptime(expected_date_str,"%Y-%b-%d_%Hh%Mm%Ss"))

    #------------------------------------------------------------------------------------------------
    # @unittest.skip("because I said so")
    def test_a3_find_session(self):
        print('\n================================================================================================')
        print('[ Testing a3: session.find_session ]')

        session_list = [
            Session("01_2022-Apr-11_05h50m32s"),
            Session("02_2022-Apr-11_07h18m15s"),
            Session("03_2022-Apr-11_07h20m12s"),
            Session("04_2022-Apr-11_07h31m49s"),
            Session("99_2021-Jul-24_01h59m59s"),
        ]

        bogus_name = 'wefaef'
        sess_obj = find_session(bogus_name, session_list)
        self.assertIsNone(sess_obj)

        sess_name = '03_2022-Apr-11_07h20m12s'
        sess_obj = find_session(sess_name, session_list)
        self.assertEqual(sess_name,sess_obj.basename)

        sess_name = '99_2021-Jul-24_01h59m59s'
        sess_obj = find_session(sess_name, session_list)
        self.assertEqual(sess_name,sess_obj.basename)

#------------------------------------------------------------------------------------------------
    # @unittest.skip("because I said so")
    def test_a4_get_all_sessions(self):
        print('\n================================================================================================')
        print('[ Testing a4: session.get_all_sessions ]')
        sessions, min_session_id, max_session_id = get_all_sessions(drives=g.paths['hdd'])
        print(f'min_session_id: {min_session_id}, max_session_id: {max_session_id}')
        for sess in sessions:
           print(sess._str_long(indent=3))

if __name__ == '__main__':
    unittest.main()