import threading
import random
import time
import multiprocessing
import sys
import os

import vlc
import requests
from requests.auth import HTTPBasicAuth
from pathlib import Path

from datetime import datetime
from utils.dirmonitor import DirMonitor
from global_vars import g
import utils.vidlogging as vidlogging
from DriveManager import DriveManager
from RecordingProcess import RecordingProcess
from utils import fileutils

logger = vidlogging.get_logger(__name__,filename=g.paths['logfile'])

class DeviceRecorder():
    ''' Handles audio and video recording for one workstation
        For video it manages both the main and overlap RecordingProcesses
    '''

    # class variables shared by all instances of DeviceRecorder
    best_drive = g.paths['viddir'] # current drive being used
    device_picking_best_drive = False # only one DeviceRecorder is allowed to make a drive switch at a time, this flag keeps them in check
    overlap_duration_min = g.advanced['video_chapters_overlap_in_minutes']
    ws_count = 0

    def __init__(self, workstation_info, sdpdir, chapter_duration_min=0):

        DeviceRecorder.ws_count = DeviceRecorder.ws_count + 1
        self.id      = int(workstation_info['id'])
        self.ws_id   = f'ws{self.id:02}'
        self.name    = f'Workstation {self.id}'
        self.ip      = workstation_info['ip']
        self.session_dir_fullpath = workstation_info['dir'] # should be session directory, abs path
        self.session_dir_basename = os.path.basename(self.session_dir_fullpath)

        # sdp vars
        self.sdp_file = f"{self.ws_id}.sdp"
        self.sdp_dir = sdpdir
        self.sdp_orig  = os.path.join(self.sdp_dir,f'{self.ws_id}.sdp')
        self.sdp_video = os.path.join(self.sdp_dir,f'{self.ws_id}_video.sdp')
        self.sdp_audio = os.path.join(self.sdp_dir,f'{self.ws_id}_audio.sdp')
        self.sdp_downloaded = False

        # Recording related vars
        self.started = False
        self.chapter_id = 0
        self.chapter_duration_min = chapter_duration_min
        self.chapter_main = None
        self.chapter_overlap = None
        self.tmonitor = -1 # last time monitor updated us, just a second counter
        self.total_vid_size = 0
        self.last_update_stats = None # last chapter_stats package used to update this Device

        logger.info(f'__init__ -> \n{self}')

    def get_info(self):
        '''Returns dict with information about this workstation (or device)'''
        process_info = self.get_process_info() # should be one for each RecordingProcess
        device_info = {
            'wsid_int': self.id,
            'wsid_str': self.ws_id,
            'ip': self.ip,
            'session_dir_basename': self.session_dir_basename,
            'session_dir_fullname': self.session_dir_fullpath,
            # 'is_recording': self.started and not self.kill_sent and (filestats and filestats['size'] > 0),
            'is_recording': self.started and self.chapter_main and self.chapter_main.record_active,
            'sdp_downloaded': self.sdp_downloaded,
            'sdp_orig'    : self.sdp_orig,
            'sdp_video'   : self.sdp_video,
            'sdp_audio'   : self.sdp_audio,
            'tmonitor'    : self.tmonitor,
            'last_update_stats': self.last_update_stats,
            'current_state': self.get_current_state(),
            'process_info': process_info,
            'chapter_count': self.last_update_stats['chapter_count'] if self.last_update_stats else 0,
            'chapter_size_main': self.get_chapter_size(process_info, 'main'),
            'chapter_size_overlap': self.get_chapter_size(process_info, 'overlap'),
            'total_vid_size': self.total_vid_size,
            'short_desc': self.short_desc(),
        }
        return device_info

    def short_desc(self):
        line =  f'wid: {self.id}, t: {self.tmonitor}, state: {self.get_current_state()}\n'
        line += f'   main    : {self.chapter_main.one_line_desc() if self.chapter_main else None}\n'
        line += f'   overlap : {self.chapter_overlap.one_line_desc() if self.chapter_overlap else None}\n'
        return line

    def get_process_info(self):
        '''Returns dicts for each recording process with information about the files
           that are being recorded for this workstation
        '''
        process_info = {
            'main': self.chapter_main.get_info() if self.chapter_main else None,
            'overlap': self.chapter_overlap.get_info() if self.chapter_overlap else None
        }

        return process_info

    def get_chapter_size(self,process_info, process_type ):
        return process_info[process_type]['chapter_size'] if process_info[process_type] else -1

    def start_recording(self, monitor=False):
        '''Start recording for this workstation'''
        if (self.started):
            return False
        logger.info(f"Workstation {self.id} : START recording.")
        self.started = True
        self.record_start()
        return True

    def stop_recording(self):
        '''Stop recording for this workstation'''
        logger.info(f"Workstation {self.id} : STOP recording.")
        if self.chapter_overlap:
            self.chapter_overlap.permission_to_stop = True # not strictly necessary but just for clarity
            self.chapter_overlap.record_stop()
            self.chapter_overlap = None
        if self.chapter_main:
            self.chapter_main.permission_to_stop = True # not strictly necessary but just for clarity
            self.chapter_main.record_stop()
            self.chapter_main = None

        self.started = False

    def check_drive_capacity(self):
        '''Allows a device to figure out which drive to store it's current vid file'''
       
        if not DeviceRecorder.device_picking_best_drive:
            DeviceRecorder.device_picking_best_drive = True

            # if active drive is in warning range we make a call to DriveManager.pick_best_drive
            active_drive = DeviceRecorder.best_drive
            drive_stats = DriveManager.get_video_storage_stats(active_drive)
            for dstat in drive_stats:
                if dstat['drive'] == DeviceRecorder.best_drive and dstat['actual_pct_used_warning'] == True:

                    # Note this also frees space if needed
                    logger.debug(f'BEFORE pick_best_drive2 -- DeviceRecorder.best_drive: {DeviceRecorder.best_drive}')
                    best_drive, max_session_id = \
                        DriveManager.pick_best_drive2(DeviceRecorder.best_drive,n_workstations=DeviceRecorder.ws_count)

                    # Did DriveManager choose a different drive to start recording on?
                    if best_drive != DeviceRecorder.best_drive:
                        logger.debug("=============================================================================================")
                        logger.debug(f'             CHANGE OF DRIVE FROM {DeviceRecorder.best_drive} to {best_drive}')
                        logger.debug("=============================================================================================")
                        DeviceRecorder.best_drive = best_drive
                    logger.debug(f'AFTER pick_best_drive2 -- DeviceRecorder.best_drive: {DeviceRecorder.best_drive}')

            DeviceRecorder.device_picking_best_drive = False
        else:
            logger.debug(f"Workstation {self.id} : {threading.current_thread().name} : WAITING FOR BEST DRIVE TO BE PICKED")
            while DeviceRecorder.device_picking_best_drive:
                pass
            logger.debug(f"Workstation {self.id} : {threading.current_thread().name} : BEST DRIVE HAS BEEN PICKED {DeviceRecorder.best_drive}")

    # def stop_chunking(self):
    #     logger.debug("=============================================================================================")
    #     logger.debug(f"STOP CHUNKING : Workstation {self.id} : {threading.current_thread().name} ")

    #     self.kill_video_subprocess()

    #     # Start the next chunk process
    #     logger.debug(f'STOP CHUNKING : DeviceRecorder.best_drive: {DeviceRecorder.best_drive}')
    #     logger.debug(f'STOP CHUNKING : DeviceRecorder.device_picking_best_drive: {DeviceRecorder.device_picking_best_drive}')
    #     logger.debug(f'STOP CHUNKING : self.session_dir_basename: {self.session_dir_basename}')
    #     logger.debug(f'STOP CHUNKING : self.session_dir_fullpath: {self.session_dir_fullpath}')

    #     self.check_drive_capacity()

    #     # Create path to session dir on the drive where we are storing the next chunk
    #     self.session_dir_fullpath = os.path.join(DeviceRecorder.best_drive,self.session_dir_basename)
    #     if not os.path.isdir(self.session_dir_fullpath):
    #           os.mkdir(self.session_dir_fullpath)

    #     # Create name of next file chunk
    #     self.chunk_id += 1
    #     self.vid_basename = f"{self.ws_id}_{self.chunk_id:04}_0.mp4"
    #     self.vid_current = os.path.join(self.session_dir_fullpath,self.vid_basename)
    #     logger.debug(f'self.vid_current: {self.vid_current}')

    #     # Start the next chunk!!!!!
    #     self.record_video()

    def record_audio(self):
        vlcapp = '/usr/bin/cvlc'
        sdpFile = f'{self.sdp_dir}/ws{1}_audio.sdp'
        print('record_audio: ' + sdpFile)
        self.audio_subprocess = subprocess.Popen([vlcapp, '--verbose="1"', sdpFile, f'--sout=file/ogg:{self.session_dir_fullpath}/{self.ws_id}.ogg'])

    def create_chapter_process(self,chapter_id,duration_min):
        return RecordingProcess(self.id,self.sdp_video,self.session_dir_fullpath,chapter_id=chapter_id,chapter_duration_min=duration_min)

    def record_start(self):
        ''' Create and start chapter_main RecordingProcess
        '''
        self.chapter_id = 0
        self.chapter_main = self.create_chapter_process(self.chapter_id,self.chapter_duration_min)
        self.chapter_main.record_start()

    def quick_info(self):
        info = f'Device: {self.id}\n'
        info += f'chapter_main    -- {self.chapter_main}'
        info += f'chapter_overlap -- {self.chapter_overlap}'
        # if self.chapter_main:
        #     info += f'chapter_main -- pid: {chapter.video_subprocess.pid} -- ' + \
        #             f'kill_count: {chapter.kill_count} -- file: {chapter.vid_basename}\n'
        # if self.chapter_overlap:
        #     info += f'chapter_overlap -- pid: {chapter.video_subprocess.pid} -- ' + \
        #             f'kill_count: {chapter.kill_count} -- file: {chapter.vid_basename}\n'
        logger.debug(info)

    def get_current_state(self):

        state = (-1,'unknown')

        # Does chapter_main exist? If not bug out
        if not self.chapter_main:
            state = (0,'no_processes') # TODO: assert that overlap is also None
        elif self.chapter_main.idle:
            state = (1,'main: idle, overlap: None') # TODO: assert that overlap is also None
        elif self.chapter_main.record_trying:
            state = (2,'main: trying, overlap: None') # TODO: assert that overlap is also None
        elif self.chapter_main.record_active and not self.chapter_overlap:
            state = (3,'main: active, overlap: None')
        elif self.chapter_main.record_active and self.chapter_overlap.record_trying:
            state = (4,'main: active, overlap: trying')
        elif self.chapter_main.record_active and self.chapter_overlap.record_active:
            state = (5,'main: active, overlap: active')
        elif self.chapter_main.record_complete and not self.chapter_overlap:
            state = (6,'main: complete, overlap: None')
        elif self.chapter_main.record_complete and self.chapter_overlap.record_trying:
            state = (7,'main: complete, overlap: trying')
        elif self.chapter_main.record_complete and self.chapter_overlap.record_active:
            state = (8,'main: complete, overlap: active')
        # TODO: STATE ERROR CONDITIONS
        # TODO: assert that both main and overlap are not complete, this should never occur
        # TODO: assert that overlap does not exist when main is None, idle, or trying
        return state

    # DeviceRecorder
    def record_update(self,stats):
        ''' Handle file stats returned by VidDirMonitor at regular intervals
        '''
        
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

        logger.debug('-----------------------------------------------------------------------------------------------')
        logger.debug(f'DeviceRecorder::record_update -- {threading.current_thread().name} -- called from dir_monitor_update_callback')


        self.last_update_stats = stats
        self.tmonitor = stats['time'] # current VidDirMonitor time count
        self.total_vid_size = stats['size']  # total size of all chapters combined. TODO: Subtract out overlap portions

        # --------------------------------------------------------------------------------------------
        # First thing, we pass the stats to the RecordingProcesses and let them update themselves
        logger.debug('BEFORE RecordingProcess record_update')
        self.quick_info()

        if self.chapter_main:
            self.chapter_main.record_update(stats)
        if self.chapter_overlap:
            self.chapter_overlap.record_update(stats)

        logger.debug('AFTER RecordingProcess record_update')
        self.quick_info()

        # --------------------------------------------------------------------------------------------
        # overlap_interval_min = .5 # how many minutes do we want to overlap?
        
        (state,state_desc) = self.get_current_state()

        # Does chapter_main exist? If not bug out
        if not self.chapter_main:
            logger.debug(state_desc)
            return

        # Is chapter_main recording yet? If not do nothing and return
        if self.chapter_main.idle or self.chapter_main.record_trying:
            logger.debug(state_desc)
            return

        # Cases where main is actively recording
        if self.chapter_main.record_active:

            # Case 3: main record_active and no overlap -- IS IT TIME TO START OVERLAP??
            if not self.chapter_overlap:
                logger.debug('Case 3: main record_active and no overlap -- IS IT TIME TO START OVERLAP??')
                # check time_left and create overlap process if it's time
                time_left = self.chapter_main.get_time_left(tmonitor=self.tmonitor)
                logger.debug(f'time_left: {time_left}')
                if time_left <= (DeviceRecorder.overlap_duration_min*60):
                    logger.debug('****************** STARTING OVERLAP PROCESS ******************')
                    self.chapter_main.permission_to_stop = False # lock it until overlap is recording successfully

                    logger.debug(f'BEFORE check_drive_capacity() -- DeviceRecorder.best_drive: {DeviceRecorder.best_drive}')
                    self.check_drive_capacity()
                    logger.debug(f'AFTER check_drive_capacity() -- DeviceRecorder.best_drive: {DeviceRecorder.best_drive}')

                    # Create path to session dir on the drive where we are storing the next chunk
                    self.session_dir_fullpath = os.path.join(DeviceRecorder.best_drive,self.session_dir_basename)
                    if not os.path.isdir(self.session_dir_fullpath):
                        fileutils.dcp_mkdir(self.session_dir_fullpath,g.log['group'],g.log['permissions'])

                    # Start overlap chapter process
                    self.chapter_id += 1
                    self.chapter_overlap = self.create_chapter_process(self.chapter_id,duration_min=self.chapter_duration_min)
                    self.chapter_overlap.record_start()

            # Case 4: main record_active and overlap trying -- NO ACTION
            elif self.chapter_overlap.record_trying:
                logger.debug('Case 4: main record_active and overlap trying -- NO ACTION')

            # Case 5: main record_active and overlap active -- UNLOCK RECORD STOP PERMISSION FOR MAIN
            elif self.chapter_overlap.record_active:
                logger.debug('Case 5: main record_active and overlap active')
                # Make sure chapter_main DOES have permission to stop
                self.chapter_main.permission_to_stop = True

        # Cases where main is finished recording
        elif self.chapter_main.record_complete:

            # Case 6: main record_complete and no overlap -- NO ACTION
            if not self.chapter_overlap:
                logger.debug('Case 6: main record_complete and no overlap -- NO ACTION')
                # nothing to do here

            # Case 7: main record_complete and overlap trying -- SHOULD NEVER OCCUR
            if self.chapter_overlap.record_trying:
                logger.debug('Case 7: main record_complete and overlap trying -- SHOULD NEVER OCCUR')
                # This should never occur since main does not have permission to stop while overlap trying
                logger.debug('MAIN FINISHED WHILE OVERLAP TRYING!!!!! WARNING THIS SHOULD NEVER HAPPEN')

            # Case 8: main record_complete and overlap active -- OVERLAP BECOMES MAIN, OVERLAP BECOMES NONE
            if self.chapter_overlap.record_active:
                logger.debug('Case 8: main record_complete and overlap active -- OVERLAP BECOMES MAIN, OVERLAP BECOMES NONE')
                self.chapter_main = self.chapter_overlap
                self.chapter_main.set_chapter_duration(self.chapter_duration_min)
                self.chapter_overlap = None

    def get_sdp_file(self,ws_id, workstation_ip):
        ''' GET the sdp file from the RNA device '''

        # GET the sdp file from the RNA device. r.content will contain the payload
        # Note: password 'ineevoro' is unclassified and does not need to be obfusciated
        logger.debug(f'workstation_ip: {workstation_ip}')
        uri = f'https://{workstation_ip}/dapi/media_v1/resources/encoder0/session/?command=get';
        logger.debug(f'uri: {uri}')
        r = requests.get(uri,auth=HTTPBasicAuth('admin','ineevoro'),verify=False,timeout=1)
        logger.debug(f'r.status_code: {r.status_code}')

        if (r.status_code == 200):
            
            group = g.log['group']
            permissions = g.log['permissions']

            # Save out sdp file to text
            original_sdp_filename = f'{ws_id}.sdp'
            original_sdp_fullpath = f'{self.sdp_dir}/{original_sdp_filename}' # p = f'prac/{file_name}'
            logger.debug(f'saving sdp file to {original_sdp_fullpath}')
            with open(original_sdp_fullpath,'wb') as writer: # save it out as text .sdp file
                writer.write(r.content)
            fileutils.dcp_tryto_set_credentials(original_sdp_fullpath,group,permissions)

            # Read in sdp file and strip all extraneous data and save back out as *_video.sdp
            parsed_sdp_filename = f'{ws_id}_video.sdp'
            parsed_sdp_fullpath_video = f'{self.sdp_dir}/{parsed_sdp_filename}'
            text = self.parse_sdp_file(sdpfile=original_sdp_fullpath,screen='screen0')
            with open(parsed_sdp_fullpath_video,'w') as writer:
                writer.write(text)
            fileutils.dcp_tryto_set_credentials(parsed_sdp_fullpath_video,group,permissions)

            # Parse sdp for audio stream information. Save out as *_audio.sdp
            audio_sdp_filename = f'{ws_id}_audio.sdp'
            parsed_sdp_fullpath_audio = f'{self.sdp_dir}/{audio_sdp_filename}'
            text = self.parse_sdp_file_audio(sdpfile=original_sdp_fullpath)
            with open(parsed_sdp_fullpath_audio,'w') as writer:
                writer.write(text)
            fileutils.dcp_tryto_set_credentials(parsed_sdp_fullpath_audio,group,permissions)

        return r.status_code == 200, original_sdp_fullpath, parsed_sdp_fullpath_video, parsed_sdp_fullpath_audio


    def parse_sdp_file_audio(self,sdpfile=""):
        '''Parse the sdp file for audio stream information
          The RNA can be configured to encode multiple types of streams. The only
          stream we are concerned with here is the audio stream. It is necessary to parse
          out the relevant lines from the sdp file so that VLC knows which stream
          to record.
        '''
        path = Path(sdpfile)
        sdp = path.read_text()
        sdpArray = sdp.split('\n')

        # start with template
        finalSDP =  "v=0\r\n" + \
                    "t=0 0\r\n"

        for i, line in enumerate(sdpArray):
            if line.startswith("o="):
                finalSDP += line + "\r\n"
          # elif line.startswith("c="):
          #   if (i + 1 < len(sdpArray) and "b=AS:12000" in sdpArray[i + 1]):
          #     finalSDP += line + "\r\n"

        audio_portion = \
            'm=audio 5004 RTP/AVP 96\r\n' + \
            'c=IN IP4 239.163.128.5/1\r\n' + \
            'a=rtpmap:96 L16/48000/2\r\n' + \
            'a=sendonly\r\n' + \
            'a=label:serverLineIn\r\n'

        finalSDP += audio_portion

        return finalSDP

    def parse_sdp_file(self,sdpfile="",screen="screen0"): # screen is 'screen0' or 'screen1'
        '''Parse the sdp file
          The RNA can be configured to encode multiple types of streams. The only
          stream we are concerned with is the H264 stream. It is necessary to parse
          out the relevant lines from the sdp file so that VLC knows which stream
          to play and record.
        '''
        path = Path(sdpfile)
        sdp = path.read_text()
        sdpArray = sdp.split('\n')

        # start with template
        finalSDP = ""

        # Record session-level lines (according to spec these are required)
        for i, line in enumerate(sdpArray):
            if line.startswith("v="):
                finalSDP += line + "\r\n"
            elif line.startswith("o="):
                finalSDP += line + "\r\n"
            elif line.startswith("s="):
                finalSDP += line + "\r\n"
            elif line.startswith("t="):
                finalSDP += line + "\r\n"

        # Record media-level lines
        h264_media_block_found = False
        h264line = 'a=rtpmap:96 H264/90000'
        media_lines = []
        in_media_block = False
        for i, line in enumerate(sdpArray):
            if line.startswith("m="):
                in_media_block = True
                if not h264_media_block_found:
                    media_lines = []
                else:
                    break
            if h264line == line:
                h264_media_block_found = True

            if in_media_block:
                media_lines.append(line)

        for line in media_lines:
            finalSDP += line + "\r\n"
        finalSDP = finalSDP.rstrip()

        return finalSDP

    def download_sdp(self):
        success, orig_sdp, vid_sdp, aud_sdp = self.get_sdp_file(self.ws_id,self.ip)
        self.sdp_downloaded = success
        if success:
            logger.info('download_sdp successful')
            logger.info(f'orig_sdp: {orig_sdp}')
            logger.info(f'vid_sdp: {vid_sdp}')
            logger.info(f'aud_sdp: {aud_sdp}')
        else:
            logger.info('download sdp unsuccessful')
        return success, orig_sdp, vid_sdp, aud_sdp

    def __str__(self):
        s = self.__dict__["name"] + ": "
        for (key, value) in self.__dict__.items():
            if (key == "name"):
                continue
            s += f"'{key}': '{value}',"
        s = s[0:-1]
        return s

if __name__ == "__main__":
    print('-------------------- Testing DeviceRecorder Class --------------------')

    session_dir = '/home/cholland/devrepo/vidrecorder/test123'

    session_sdp_dir = os.path.join(session_dir,'sdp')
    if not os.path.isdir(session_sdp_dir):
        fileutils.dcp_mkdir(session_sdp_dir,g.log['group'],g.log['permissions'])


    workstations = []
    ipAdresses = ['192.168.5.72']
    for ip in ipAdresses:
        workstation_valid_ping = True
        workstations.append(
            {
                "id": int(ip[-2:]) % 70 if len(ip) > 2 else -1,
                "ip": ip,
                "valid_ping": workstation_valid_ping,
                "dir": session_dir
            }
        )

    device_list = []

    workstation_info = []
    n = len(workstations) # number of selected workstations
    sdp_download_failed = [False for i in range(n)]
    chapter_duration_min = g.advanced['video_chapters_duration_in_minutes'] if g.advanced['video_chapters_enabled'] else 0
    for i in range(n):
        d = DeviceRecorder(workstations[i],sdpdir=session_sdp_dir,chapter_duration_min=chapter_duration_min)
        w = d.get_workstation_info()
        try:
            success, orig_sdp, vid_sdp, aud_sdp = d.download_sdp()
            device_list.append(d) # note if the sdp download fails then the device will
                                  # never be added to list...that is the behavior we want
        except:
            logger.error('SDP download failed')
            success = False
            sdp_download_failed[i] = True
        w['sdp_downloaded'] = success
        workstation_info.append(w)

    for d in device_list:
        d.start_recording()