import threading
import logging
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
from utils.filemonitor import FileMonitor
from utils.dirmonitor import DirMonitor

format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO,
                    datefmt="%H:%M:%S")

class DeviceRecorder():
  ''' Handles audio and video recording for one workstation
  '''
  # video_file_monitor = None
  
  def __init__(self, workstation_info, sdpdir):

    self.id      = int(workstation_info['id'])
    self.ip      = workstation_info['ip']
    self.savedir = workstation_info['dir']
    self.restart_interval = workstation_info['restart_interval']
    self.workstation_num = self.id
    self.name = f"Workstation {self.id}"
    self.vid_basename = f"ws{self.id}.mp4"
    
    # Recording related vars
    self.video_subprocess_old = None
    self.video_subprocess = None # subprocess running vlc that is recording video
    self.audio_subprocess = None # subprocess running vlc that is recording audio
    self.started = False
    self.duration = -1
    self.restart_needed = False
    self.kill_sent = False
    self.restart_time = -1

    self.sdp_file = f"ws{self.id}.sdp"
    self.sdp_dir = sdpdir #'./prac/sdp'
    self.sdp_downloaded = False
    
    self.kill_count = 0
    self.filestats = None

  def get_workstation_info(self):
    filestats = self.get_filestats()
    w = {
        'id': self.id,
        'ip': self.ip,
        'savedir': self.savedir,
        'vid_basename': self.vid_basename,
        'is_recording': self.started and not self.kill_sent and filestats['size'] > 0,
        'sdp_downloaded': self.sdp_downloaded,
        'filestats': filestats}
    return w
  
  def get_filestats(self):
        filestats = None
        fullname = os.path.join(self.savedir,self.vid_basename)
        if os.path.exists(fullname):
            filestats = {
              'basename': self.vid_basename,
              'fullname': fullname,
              'time': -1,
              'size': os.path.getsize(fullname),
            }
        return filestats
  
  def start_recording(self, duration=None, monitor=False):

    if (self.started):
      return False

    self.started = True
    self.duration = duration

    logging.info(f"Thread {self.id} : start recording.")

    self.record_video()
    
    # self.video_file_monitor = FileMonitor(filepath=f'{self.savedir}/ws{self.id}.mp4',hz=1.0,logger=logging.info)
    # if monitor and DeviceRecorder.video_file_monitor:
    #   if not DeviceRecorder.video_file_monitor.running:
    #     DeviceRecorder.video_file_monitor.start()

    # if self.id == 1:
    #   self.audio_thread = threading.Thread(target=self.record_audio)
    #   self.audio_thread.start()
    
    return True

  def stop_recording(self):
    # self.quick_info()
    self.kill_video_subprocess()
    # self.quick_info()
    self.kill_audio_subprocess()
    # self.kill_video_process() # this multiprocessing.Process spawned the vlc subprocess
    self.started = False

  def record_audio(self):
    vlcapp = '/usr/bin/cvlc'
    sdpFile = f'{self.sdp_dir}/ws{1}_audio.sdp'
    print('record_audio: ' + sdpFile)
    self.audio_subprocess = subprocess.Popen([vlcapp, '--verbose="1"', sdpFile, f'--sout=file/ogg:{self.savedir}/ws{self.id}.ogg'])

  def record_video(self):
    vlcapp = '/usr/bin/cvlc'
    sdpFile = f'{self.sdp_dir}/ws{self.id}_parsed.sdp'
    output_file_param = f'--sout=file/ts:{self.savedir}/ws{self.id}.mp4'
    logging.info('DeviceRecorder::record_video --> ' + sdpFile)

    # Kill the vlc subprocess if it is still running
    # if self.video_subprocess:
    #   self.kill_video_subprocess()
      
    # Start the vlc application passing the sdpFile it needs to read the stream correctly
    cmd = f'{vlcapp} --verbose="1" {sdpFile} {output_file_param}'
    
    if self.video_subprocess:
      logging.info(f'pid: {self.video_subprocess.pid} -- Before')
    self.video_subprocess = subprocess.Popen([vlcapp,'--verbose="2"', sdpFile, f'--sout=file/ts:{self.savedir}/ws{self.id}.mp4'])
    if self.video_subprocess:
      logging.info(f'pid: {self.video_subprocess.pid} -- After')
    self.kill_sent = False
    # print(self.video_subprocess)
    # self.pid = subprocess.Popen(cmd)
    # self.pid.daemon = True
  
  # TODO: Remove returncode, add more info
  def quick_info(self):
    info = f'Device: {self.id} -- pid: {self.video_subprocess.pid} -- ' + \
           f'kill_count: {self.kill_count} -- file: {self.vid_basename} -- '
    logging.info(info)
    
  def kill_video_subprocess(self):
      
    if self.video_subprocess:
      # logging.info(f'subprocess pid: {self.video_subprocess.pid} -- kill_count: {self.kill_count} -- Terminating video_subprocess {self.vid_basename}')
      logging.info('Terminating subprocess')
      self.video_subprocess.terminate()
      self.kill_sent = True
      self.kill_count += 1
      # self.video_subprocess = None
      # logging.info('After terminating subprocess')
       
  def kill_audio_subprocess(self):
    if self.audio_subprocess:
      logging.info('Terminating audio_subprocess')
      self.audio_subprocess.terminate()
      self.audio_subprocess = None

  def handle_file_check(self,stats):
      ''' Handle file stats returned by DirMonitor at regular intervals
      '''
      self.filestats = stats
      fullname = stats['fullname']
      basename = os.path.basename(fullname)
      t = stats['time']
      filesize = stats['size']
      output = ""
      if not os.path.exists(fullname):
          output += f"T: {t:.03} -- File: {basename} -- doesn't exist\n"
      else:
          output += f"T: {t:.03} -- File: {basename} -- sz: {stats['size']} -- restart_time: {t % self.restart_interval}"
      print(output)

      self.restart_needed = (filesize == 0 and (t % self.restart_interval) == 0)

      if self.restart_needed:
          if not self.kill_sent:
            self.kill_video_subprocess()

      if self.kill_sent:
          if self.video_subprocess.poll() is None: # make sure process has finished terminiating before recreating
              logging.info(f"Waiting for vlc process {self.video_subprocess.pid} to terminate...")
          else:
              logging.info("Restarting vlc process ...")
              self.record_video() # start the vlc process up again


  def get_sdp_file(self,workstation_num, workstation_ip):
    ''' GET the sdp file from the RNA device '''

    # GET the sdp file from the RNA device. r.content will contain the payload
    print(workstation_ip)
    uri = f'https://{workstation_ip}/dapi/media_v1/resources/encoder0/session/?command=get';
    print(uri)
    r = requests.get(uri,auth=HTTPBasicAuth('admin','ineevoro'),verify=False,timeout=1)
    print(f'r.status_code: {r.status_code}')

    if (r.status_code == 200):

        # Save out sdp file to text
        original_sdp_filename = f'ws{workstation_num}.sdp'
        p = f'{self.sdp_dir}/{original_sdp_filename}' # p = f'prac/{file_name}'
        print(f'saving sdp file to {p}')
        open(p,'wb').write(r.content) # save it out as text .sdp file

        # Read in sdp file and strip all extraneous data and save back out as *_parsed.sdp
        parsed_sdp_filename = f'ws{workstation_num}_parsed.sdp'
        path_to_file = f'{self.sdp_dir}/{parsed_sdp_filename}'
        text = self.parse_sdp_file(sdpfile=p,screen='screen0')
        with open(path_to_file,'w') as writer:
            writer.write(text)

        # Parse sdp for audio stream information. Save out as *_audio.sdp
        audio_sdp_filename = f'ws{workstation_num}_audio.sdp'
        path_to_file = f'{self.sdp_dir}/{audio_sdp_filename}'
        text = self.parse_sdp_file_audio(sdpfile=p)
        with open(path_to_file,'w') as writer:
            writer.write(text)

    return r.status_code == 200, path_to_file


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
  
  # def start_vid_monitor(self):
  #   self.vlc_inspect_timer = threading.Timer(1.0, self.show_vlc_data)
  #           self.vlc_inspect_timer.start()

  def download_sdp(self):
    success, sdp_path = self.get_sdp_file(self.workstation_num,self.ip)
    self.sdp_downloaded = success
    return success
    # num_rna = 5
    # octet = 70 + (self.workstation_num) + int((self.workstation_num-1) / num_rna)
    # workstation_ip = f'192.168.5.{octet}'
    # if self.workstation_num <= num_rna:
    #   success, sdp_path = self.get_sdp_file(self.workstation_num,workstation_ip)
    #   self.sdp_downloaded = success
    # else:
    #   self.sdp_downloaded = True

  def __str__(self):
    s = self.__dict__["name"] + ": "
    for (key, value) in self.__dict__.items():
        if (key == "name"):
            continue
        s += f"'{key}': '{value}',"
    s = s[0:-1]
    return s
