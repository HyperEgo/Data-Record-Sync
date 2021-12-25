import threading
import random
import time
import subprocess
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

# format = "%(asctime)s: %(message)s"
# logging.basicConfig(format=format, level=logging.INFO,
#                     datefmt="%H:%M:%S")

logger = vidlogging.get_logger(__name__,filename=g.paths['logfile'])

class DeviceRecorder():
  ''' Handles audio and video recording for one workstation
  '''

  # class variables shared by all instances of DeviceRecorder
  best_drive = g.paths['viddir'] # current drive being used
  device_picking_best_drive = False # only one DeviceRecorder is allowed to make a drive switch at a time, this flag keeps them in check

  def __init__(self, workstation_info, sdpdir, chunk_duration_min=0):

    self.id      = int(workstation_info['id'])
    self.ws_id   = f'ws{self.id:02}'
    self.ip      = workstation_info['ip']
    self.session_dir_fullpath = workstation_info['dir'] # should be session directory
    self.session_dir_basename = os.path.basename(self.session_dir_fullpath)
    self.restart_interval = workstation_info['restart_interval']
    self.workstation_num = self.id
    self.name = f"Workstation {self.id}"
    
    # Recording related vars
    self.video_subprocess = None # subprocess running vlc that is recording video
    self.audio_subprocess = None # subprocess running vlc that is recording audio
    self.started = False
    self.trying = False
    self.duration = -1
    self.restart_needed = False
    self.kill_sent = False
    self.kill_count = 0
    self.restart_time = -1
    self.filestats = None
    self.chunk_thread = None
    self.chunk_duration_min = chunk_duration_min # record video in seperate vid files of length chunk_duration_min, if zero just record one long vid.
    self.chunk_id = 0
    self.stop_chunk_at_time = -1
    if self.chunk_duration_min > 0:
        self.vid_basename = f"{self.ws_id}_{self.chunk_id:04}_0.mp4"
    else:
        self.vid_basename = f"{self.ws_id}.mp4"
    self.vid_current = os.path.join(self.session_dir_fullpath,self.vid_basename)
    print(f'self.vid_current: {self.vid_current}')

    # sdp vars
    self.sdp_file = f"{self.ws_id}.sdp"
    self.sdp_dir = sdpdir
    self.sdp_orig  = os.path.join(self.sdp_dir,f'{self.ws_id}.sdp')
    self.sdp_video = os.path.join(self.sdp_dir,f'{self.ws_id}_video.sdp')
    self.sdp_audio = os.path.join(self.sdp_dir,f'{self.ws_id}_audio.sdp')
    self.sdp_downloaded = False

    logger.info(f'__init__ -> {self}')

  def get_workstation_info(self):
    '''Returns dict with information about this workstation (or device)'''
    filestats = self.get_filestats()
    w = {
        'id': self.id,
        'ip': self.ip,
        'session_dir_basename': self.session_dir_basename,
        'session_dir_fullpath': self.session_dir_fullpath,
        'vid_basename': self.vid_basename,
        'vid_current' : self.vid_current,  # path to current video file being recorded to
        'is_recording': self.started and not self.kill_sent and (filestats and filestats['size'] > 0),
        'sdp_downloaded': self.sdp_downloaded,
        'sdp_orig'    : self.sdp_orig,
        'sdp_video'   : self.sdp_video,
        'sdp_audio'   : self.sdp_audio,
        'filestats': filestats
    }
    return w

  def get_filestats(self):
    '''Returns dict with information about the file that is being recorded for this workstation'''
    filestats = None
    fullname = self.vid_current
    # print(f'get_filestats -- fullname {fullname}')
    if os.path.exists(fullname):
        filestats = {
          'basename': self.vid_basename,
          'fullname': fullname,
          'time': -1,
          'size': os.path.getsize(fullname),
        }
    # print(f'get_filestats -- filestats {filestats}')
    return filestats

  def start_recording(self, duration=None, monitor=False):

    if (self.started):
        return False

    self.started = True
    self.duration = duration

    logger.info(f"Workstation {self.id} : START recording.")

    self.record_video()

    return True

  def stop_recording(self):

      logger.info(f"Workstation {self.id} : STOP recording.")
      # self.quick_info()
      self.kill_video_subprocess()
      # self.quick_info()
      self.kill_audio_subprocess()
      # self.kill_video_process() # this multiprocessing.Process spawned the vlc subprocess
      self.started = False
      self.trying = False
      if self.chunk_thread:
          self.chunk_thread.cancel()

  def check_drive_capacity(self):
      '''Allows a device to figure out which drive to store it's current vid file'''
      if not DeviceRecorder.device_picking_best_drive:
          DeviceRecorder.device_picking_best_drive = True

          drive_stats = DriveManager.get_video_storage_stats(DeviceRecorder.best_drive)
          for dstat in drive_stats:
              if dstat['drive'] == DeviceRecorder.best_drive and dstat['actual_pct_used_warning'] == True:
                  best_drive, max_session_id = DriveManager.pick_best_drive(DeviceRecorder.best_drive,n_workstations=5) # TODO remove hardcoding
                  if best_drive != DeviceRecorder.best_drive:
                        logger.debug("=============================================================================================")
                        logger.debug(f'             CHANGE OF DRIVE FROM {DeviceRecorder.best_drive} to {best_drive}')
                        logger.debug("=============================================================================================")
                        DeviceRecorder.best_drive = best_drive

          DeviceRecorder.device_picking_best_drive = False
      else:
          logger.debug(f"Workstation {self.id} : {threading.current_thread().name} : WAITING FOR BEST DRIVE TO BE PICKED")
          while DeviceRecorder.device_picking_best_drive:
              pass
          logger.debug(f"Workstation {self.id} : {threading.current_thread().name} : BEST DRIVE HAS BEEN PICKED {DeviceRecorder.best_drive}")
          
  def stop_chunking(self):
      logger.debug("=============================================================================================")
      logger.debug(f"STOP CHUNKING : Workstation {self.id} : {threading.current_thread().name} ")
      
      self.kill_video_subprocess()

      # Start the next chunk process
      logger.debug(f'STOP CHUNKING : DeviceRecorder.best_drive: {DeviceRecorder.best_drive}')
      logger.debug(f'STOP CHUNKING : DeviceRecorder.device_picking_best_drive: {DeviceRecorder.device_picking_best_drive}')
      logger.debug(f'STOP CHUNKING : self.session_dir_basename: {self.session_dir_basename}')
      logger.debug(f'STOP CHUNKING : self.session_dir_fullpath: {self.session_dir_fullpath}')

      self.check_drive_capacity()

      # Create path to session dir on the drive where we are storing the next chunk
      self.session_dir_fullpath = os.path.join(DeviceRecorder.best_drive,self.session_dir_basename)
      if not os.path.isdir(self.session_dir_fullpath):
            os.mkdir(self.session_dir_fullpath)
      
      # Create name of next file chunk
      self.chunk_id += 1
      self.vid_basename = f"{self.ws_id}_{self.chunk_id:04}_0.mp4"
      self.vid_current = os.path.join(self.session_dir_fullpath,self.vid_basename)
      logger.debug(f'self.vid_current: {self.vid_current}')

      # Start the next chunk!!!!!
      self.record_video()

  def record_audio(self):
    vlcapp = '/usr/bin/cvlc'
    sdpFile = f'{self.sdp_dir}/ws{1}_audio.sdp'
    print('record_audio: ' + sdpFile)
    self.audio_subprocess = subprocess.Popen([vlcapp, '--verbose="1"', sdpFile, f'--sout=file/ogg:{self.session_dir_fullpath}/{self.ws_id}.ogg'])

  def record_video(self):
    ''' Creates vlc subprocess to record the video using parsed sdp file
    '''
    vlcapp = '/usr/bin/cvlc'
    sdpFile = self.sdp_video
    video_file_path = self.vid_current
    video_file_param = f'--sout=file/ts:{video_file_path}'
    logger.debug('record_video --> ' + sdpFile)

    # Start the vlc application passing the sdpFile it needs to read the stream correctly
    cmd = f'{vlcapp} --verbose="2" {sdpFile} {video_file_param}'

    if self.video_subprocess:
      logger.debug(f'pid: {self.video_subprocess.pid} -- Before')

    self.video_subprocess = subprocess.Popen(cmd.split())

    if self.video_subprocess:
      logger.debug(f'pid: {self.video_subprocess.pid} -- After')

    self.trying = True
    self.stop_chunk_at_time = -1 # reset, this will be set once the filesize is verified > 0 in handle_file_check
    self.kill_sent = False
    self.kill_count = 0

  def quick_info(self):
    info = f'Device: {self.id} -- pid: {self.video_subprocess.pid} -- ' + \
           f'kill_count: {self.kill_count} -- file: {self.vid_basename} -- '
    logger.debug(info)

  def kill_video_subprocess(self):

    if self.video_subprocess:
      # logging.info(f'subprocess pid: {self.video_subprocess.pid} -- kill_count: {self.kill_count} -- Terminating video_subprocess {self.vid_basename}')
      logger.debug('Terminating subprocess')
      self.video_subprocess.terminate()
      self.kill_sent = True
      self.kill_count += 1
      # self.video_subprocess = None
      # logging.info('After terminating subprocess')
       
  def kill_audio_subprocess(self):
    if self.audio_subprocess:
      logger.info('Terminating audio_subprocess')
      self.audio_subprocess.terminate()
      self.audio_subprocess = None

  def handle_file_check(self,stats):
      ''' Handle file stats returned by VidDirMonitor at regular intervals
      '''
      # logger.debug('-----------------------------------------------------------------------------------------------')
      # logger.debug(f'DeviceRecorder::handle_file_check -- {threading.current_thread().name} -- called from dir_monitor_update_callback')
      self.filestats = stats
      wsid     = stats['wsid']
      basename = stats['basename']
      fullname = stats['fullname']
      tmonitor = stats['time']
      filesize = stats['size']
      if self.chunk_duration_min > 0: # yes we are chunking
          filesize = stats['chapter_size']
      
      # Look at stats debugging only
      output = ""
      if not os.path.exists(fullname):
          output += f"T: {tmonitor:.2f} -- File: {basename} -- doesn't exist\n"
      else:
          output += f"T: {tmonitor:.2f} -- Next chunk T: {self.stop_chunk_at_time} -- File: {basename} -- sz: {filesize} -- restart_time: {tmonitor % self.restart_interval} -- trying: {self.trying} -- {threading.current_thread().name}"
      logger.debug(output)

      # Determine if a restart of vlc process is needed
      if self.trying:

          if filesize > 0 and not self.kill_sent:
              self.trying = False # Yay!
              # if chunking start the chunk timer
              if self.chunk_duration_min > 0:
                    self.stop_chunk_at_time = tmonitor + self.chunk_duration_min*60
                  # self.chunk_thread = threading.Timer(interval=self.chunk_duration_min*60, function=self.stop_chunking)
                  # self.chunk_thread.daemon = True
                  # self.chunk_thread.start()

          self.restart_needed = (filesize == 0 and (tmonitor % self.restart_interval) == 0)

          if self.restart_needed and not self.kill_sent:
              self.kill_video_subprocess()

          if self.kill_sent:
              if self.video_subprocess.poll() is None: # make sure process has finished terminiating before recreating
                  logger.debug(f"Waiting for vlc process {self.video_subprocess.pid} to terminate...")
              else:
                  logger.debug("Restarting vlc process ...")
                  self.record_video() # start the vlc process up again

      # Determine if we need to stop this chunk and move on to the next chunk
      if self.stop_chunk_at_time > 0 and tmonitor >= self.stop_chunk_at_time:
          self.stop_chunking()


  def get_sdp_file(self,ws_id, workstation_ip):
    ''' GET the sdp file from the RNA device '''

    # GET the sdp file from the RNA device. r.content will contain the payload
    logger.debug(f'workstation_ip: {workstation_ip}')
    uri = f'https://{workstation_ip}/dapi/media_v1/resources/encoder0/session/?command=get';
    logger.debug(f'uri: {uri}')
    r = requests.get(uri,auth=HTTPBasicAuth('admin','ineevoro'),verify=False,timeout=1)
    logger.debug(f'r.status_code: {r.status_code}')

    if (r.status_code == 200):

        # Save out sdp file to text
        original_sdp_filename = f'{ws_id}.sdp'
        original_sdp_fullpath = f'{self.sdp_dir}/{original_sdp_filename}' # p = f'prac/{file_name}'
        logger.debug(f'saving sdp file to {original_sdp_fullpath}')
        with open(original_sdp_fullpath,'wb') as writer: # save it out as text .sdp file
            writer.write(r.content)

        # Read in sdp file and strip all extraneous data and save back out as *_video.sdp
        parsed_sdp_filename = f'{ws_id}_video.sdp'
        parsed_sdp_fullpath_video = f'{self.sdp_dir}/{parsed_sdp_filename}'
        text = self.parse_sdp_file(sdpfile=original_sdp_fullpath,screen='screen0')
        with open(parsed_sdp_fullpath_video,'w') as writer:
            writer.write(text)

        # Parse sdp for audio stream information. Save out as *_audio.sdp
        audio_sdp_filename = f'{ws_id}_audio.sdp'
        parsed_sdp_fullpath_audio = f'{self.sdp_dir}/{audio_sdp_filename}'
        text = self.parse_sdp_file_audio(sdpfile=original_sdp_fullpath)
        with open(parsed_sdp_fullpath_audio,'w') as writer:
            writer.write(text)

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
