import os
import subprocess
import threading

from global_vars import g
import utils.vidlogging as vidlogging
from utils import fileutils

logger = vidlogging.get_logger(__name__,filename=g.paths['logfile'])

class RecordingProcess():
    ''' Encapsulates all of the vars associated with one chapter file
    '''
    # class variables shared by all instances of RecordingProcess
    restart_interval = g.advanced['restart_interval']

    def __init__(self,wsid_int,sdp_video,session_dir_fullpath,chapter_id=0,chapter_duration_min=0):
        self.id = wsid_int
        self.ws_id   = f'ws{self.id:02}'
        self.session_dir_fullpath = session_dir_fullpath
        self.chapter_duration_min = chapter_duration_min

        self.chapter_id = -1
        self.vid_basename = ""
        self.vid_fullname = ""
        self.set_chapter_id(chapter_id) # also sets self.vid_basename and self.vid_fullname

        # Vars to control start/stopping vlc process
        self.sdp_video = sdp_video # fullpath of sdp file read from RNA for this workstation
        self.video_subprocess = None # subprocess running vlc that is recording video
        self.restart_needed = False
        self.kill_sent = False
        self.kill_count = 0
        self.tmonitor = -1 # last time monitor updated us, just a second counter
        self.stop_chapter_at_time = 0
        self.permission_to_stop = True # Parent DeviceRecorder is the only one that set this
        self.last_update_stats = None

        # State flags
        self.idle = True
        self.record_trying = False
        self.record_active = False
        self.record_complete = False

        # Verify sdp file exists
        if not self.sdp_video or not os.path.exists(self.sdp_video):
            logger.debug(f'{self.ws_id}: RecordingProcess created without valid sdp file')
            return

    def set_chapter_id(self,id):
        self.chapter_id = id
        self.vid_basename = f"{self.ws_id}_{self.chapter_id:04}_0.mp4"
        self.vid_fullname = os.path.join(self.session_dir_fullpath,self.vid_basename)

    def set_chapter_duration(self,duration):
        self.chapter_duration_min = duration
        self.stop_chapter_at_time = self.tmonitor + self.chapter_duration_min*60

    def get_info(self):
        ''' Return dict with information about this process
        '''
        # print('Inside RecordingProcess.get_info()')
        info = {
            'pid'         : self.video_subprocess.pid if self.video_subprocess else None,
            'wsid_int'    : self.id,
            'wsid_str'    : self.ws_id,
            'chapter_id'  : self.chapter_id,
            'chapter_size': os.path.getsize(self.vid_fullname) if os.path.exists(self.vid_fullname) else -1,
            'time_now'    : self.tmonitor,
            'time_left'   : self.get_time_left(self.tmonitor),
            'time_stop'   : self.stop_chapter_at_time,
            'permission_to_stop' : self.permission_to_stop,
            'restart_needed' : self.restart_needed,
            'kill_sent'   : self.kill_sent,
            'path' : {
                'vid_basename': self.vid_basename,
                'vid_fullname': self.vid_fullname,
            },
            'state': {
                'idle': self.idle,
                'record_trying': self.record_trying,
                'record_active': self.record_active,
                'record_complete': self.record_complete
            },
            'last_update_stats': self.last_update_stats,
        }

        return info

    def get_time_left(self,tmonitor=0):
        ''' Returns time left in seconds to start the next chapter file
            Returning None inidicates it's running forever
        '''
        time_to_stop = self.stop_chapter_at_time
        time_left = None
        if time_to_stop > 0 and tmonitor > 0:
            time_left = time_to_stop - tmonitor
        return time_left # None indicates it's running forever

    def record_start(self):
        ''' Creates vlc subprocess to record the video using parsed sdp file
        '''
        # Verify sdp file exists
        if not self.sdp_video or not os.path.exists(self.sdp_video):
            logger.debug(f'{self.ws_id}: RecordingProcess.record_start() called without valid sdp file. Aborting.')
            return

        vlcapp = '/usr/bin/cvlc'
        video_file_param = f'--sout=file/ts:{self.vid_fullname}'
        logger.debug(f'record_start() -- wid: {self.ws_id} -- ch: {self.chapter_id} -- sdp: {self.sdp_video}')

        # Start the vlc application passing the self.sdp_video it needs to read the stream correctly
        cmd = f'{vlcapp} --verbose="2" {self.sdp_video} {video_file_param}'

        if self.video_subprocess:
            logger.debug(f'pid: {self.video_subprocess.pid} -- Before')

        # START ER UP!!!!!!!!!!
        self.video_subprocess = subprocess.Popen(cmd.split())

        if self.video_subprocess:
            logger.debug(f'pid: {self.video_subprocess.pid} -- After')

        # Reset all of our state vars
        self.stop_chapter_at_time = -1 # reset, this will be set once the filesize is verified > 0 in record_update
        self.kill_sent = False
        self.kill_count = 0
        self.idle = False
        self.record_trying = True
        self.record_active = False
        self.record_complete = False

    def kill_video_subprocess(self):

        if self.video_subprocess:
            # logging.info(f'subprocess pid: {self.video_subprocess.pid} -- kill_count: {self.kill_count} -- Terminating video_subprocess {self.vid_basename}')
            logger.debug('Terminating subprocess')
            self.video_subprocess.terminate()
            self.kill_sent = True
            self.kill_count += 1
            # self.video_subprocess = None
            # logging.info('After terminating subprocess')
            fileutils.dcp_tryto_set_credentials(self.vid_fullname,g.log['group'],g.log['permissions'])

    def record_stop(self):
        self.kill_video_subprocess()

    # RecordingProcess
    def record_update(self,stats): # stats from DriveManager.calc_chapter_stats

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
        
        wsid     = stats['wsid']
        tmonitor = stats['time'] # current VidDirMonitor time count

        self.tmonitor = tmonitor
        self.last_update_stats = stats

        # Find the specific filestats for the chapter file being recorded by this process
        # note: stats['filestats'] is a list of dicts containing info about each chapter 
        # file associated with this workstation. The last two are really the only ones we care about.

        basename = 'unknown'
        fullname = 'unknown'
        chapter_size = 0
        filestats = stats['filestats']
        if not filestats:
            return

        for i in range(len(filestats)-1, -1, -1):
            # print(f'i: {i} -- filestats[{i}]: {filestats[i]}')
            chapter_stats = filestats[i]
            chapter_id = chapter_stats['chapter_id']
            if chapter_id == self.chapter_id:
                basename = chapter_stats['basename']
                fullname = chapter_stats['fullname']
                chapter_size = chapter_stats['chapter_size']
                break

        # Look at stats debugging only
        output = ""
        if not os.path.exists(fullname):
            output += f"T: {tmonitor:.2f} -- File: {basename} -- doesn't exist\n"
        else:
            output += f"T: {tmonitor:.2f} -- Stop T: {self.stop_chapter_at_time} -- File: {basename} -- sz: {chapter_size} -- restart_time: {tmonitor % RecordingProcess.restart_interval} -- trying: {self.record_trying} -- {threading.current_thread().name}"
        logger.debug(output)

        # Determine if a restart of vlc process is needed
        if self.record_trying:

            # Are we recording finally?
            if chapter_size > 0 and not self.kill_sent:
                self.record_trying = False # Yay! It's recording finally.
                self.record_active = True
                if self.chapter_duration_min > 0:
                    self.stop_chapter_at_time = tmonitor + self.chapter_duration_min*60

            # We are not recording yet. Check to see if we need to restart the process, otherwise just wait
            self.restart_needed = (chapter_size == 0 and (tmonitor % RecordingProcess.restart_interval) == 0)

            if self.restart_needed and not self.kill_sent:
                self.kill_video_subprocess()

            if self.kill_sent:
                if self.video_subprocess.poll() is None: # make sure process has finished terminiating before recreating
                    logger.debug(f"Waiting for vlc process {self.video_subprocess.pid} to terminate...")
                else:
                    logger.debug("Restarting vlc process ...")
                    self.record_start()

        # Determine if we need to stop this chapter
        if self.record_active:
            
            if tmonitor >= self.stop_chapter_at_time and self.permission_to_stop:
                self.record_stop()
                # Note we can't just mark the recording_complete yet. We must wait for the vlc
                # process to shut down. We can check that using self.video_subprocess.poll() 
            if self.kill_sent:
                if self.video_subprocess.poll() is None: # make sure process has finished terminiating before recreating
                    logger.debug(f"Waiting for vlc process {self.video_subprocess.pid} to terminate...")
                else:
                    logger.debug(f"!!!!!!!! Chapter {self.chapter_id} is complete !!!!!!!!!!!!!!")
                    self.record_active = False
                    self.record_complete = True

    def one_line_desc(self):
        time_left = self.get_time_left(self.tmonitor)
        pid = self.video_subprocess.pid if self.video_subprocess else None
        line = f'wid: {self.id}, cid: {self.chapter_id}, pid: {pid}, t: {self.tmonitor}, ' \
               f'ts: {self.stop_chapter_at_time}, tl: {time_left}'
        return line

    def __str__(self):
        pid = self.video_subprocess.pid if self.video_subprocess else None
        time_left = self.get_time_left(self.tmonitor)
        s = \
f"""
RecordingProcess : ws_id="{self.ws_id}", chapter_id={self.chapter_id}, pid={pid}
            Path : vid_fullname="{self.vid_fullname}"
           State : idle={self.idle}, trying={self.record_trying}, active={self.record_active}, complete={self.record_complete}
         Control : restart_needed={self.restart_needed}, kill_sent={self.kill_sent}, kill_count={self.kill_count}
           Times : stop_chapter_at_time={self.stop_chapter_at_time}, time_left={time_left}
"""
        return s

if __name__ == "__main__":
    print('-------------------- Testing RecordingProcess Class --------------------')
    sessionDir = '/home/cholland/devrepo/vidrecorder/test123'
    file_recorders = []
    file_recorders.append(RecordingProcess(1,None,sessionDir,chapter_id=23,chapter_duration_min=2))
    file_recorders.append(RecordingProcess(1,None,sessionDir,chapter_id=24,chapter_duration_min=2))
    for r in file_recorders:
        s = str(r)
        print(s)
        print('-'*80)