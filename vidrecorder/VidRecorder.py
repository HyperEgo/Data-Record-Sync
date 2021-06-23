import os
import time
import datetime
import logging
import threading
import configparser
import shutil


from global_vars import g
from DeviceRecorder import DeviceRecorder
from utils.dirmonitor import DirMonitor

class VidDirMonitor(DirMonitor):
  def __init__(self, dirpath, hz=2, logger=print, update_callback=None):
    print('VidDirMonitor')
    super().__init__(dirpath,hz,logger,update_callback)
    
  def collect_file_stats(self,t):
    print('VidDirMonitor::collect_file_stats')
    allstats = []
    filelist = []
    
    # dev mode
    if (g.dev_mode == "1" and g.dev_opts['devDirectory'] == "1"):
        filelist = os.listdir(self.dirpath)
        filelist.sort()
        for i,f in enumerate(filelist):
            filelist[i] = os.path.join(self.dirpath,f)
    # prod mode
    else: 
        dlist = os.listdir(self.dirpath)
        dlist.sort()
        print(dlist)
        for d in dlist:
            fullpath = os.path.join(self.dirpath,d)
            print(fullpath)
            if os.path.isdir(fullpath) and ("WS" in d):
                mp4 = os.listdir(fullpath)
                for f in mp4:
                  filelist.append(os.path.join(fullpath,f))
        print(filelist)

    for f in filelist:
        basename = os.path.basename(f)
        fullname = f
        stats = {
            'basename': basename,
            'fullname': fullname,
            'time': t,
            'size': os.path.getsize(fullname),
        }
        allstats.append(stats)
    return allstats
          
class VidRecorder():

  def __init__(self, wslist, savedir, sdpdir, update_callback=None, duration=None, video_monitor_on=True, use_dev_dir=True):
        
    self.use_dev_dir  = use_dev_dir
    self.wslist = wslist # list of workstation id's or ip address not sure which yet
    self.duration = duration
    self.duration_thread = None
    self.update_gui_callback = update_callback
    self.is_recording = False
    self.device_list = []
    self.sessionDirectory = None # this is the current timestamped directory where recorded data is being stored
    self.video_monitor = None
    self.video_monitor_on = video_monitor_on
    self.sdpdir = sdpdir

    (self.wslist, self.sessionDirectory) = self.create_directory_structure(savedir,self.wslist,self.use_dev_dir)

  def start(self):
      logging.info('VidRecorder start()!!!!')
      if (self.is_recording):
        return

      self.device_list = []
      workstation_info = []
      abort = False
      for i in range(len(self.wslist)):
        d = DeviceRecorder(self.wslist[i],self.sdpdir)
        w = d.get_workstation_info()
        try:
          success = d.download_sdp()
          self.device_list.append(d)
        except:
          print('SDP download failed')
          success = False
          abort = True
        w['sdp_downloaded'] = success
        workstation_info.append(w)
        
      print('Updating gui with SDP download status')
      self.update_gui_callback({
        'type': 'SDP Download Status',
        'workstation_info': workstation_info,
      })

      if abort or len(self.device_list) == 0:
        self.update_gui_callback({
          'type': 'Recording stopped',
          'workstation_info': self.get_workstation_info(),
          'duration': self.duration,
          'abort': True,
      })
        return

      # # Start duration timer here (in minutes)
      # if (self.duration is not None and self.duration > 0):
      #   self.duration_thread = threading.Timer(interval=int(self.duration*60), function=self.stop)
      #   self.duration_thread.start()

      print('WAITING FOR SDPs to download.............')
      # Wait for all of the sdp downloads to complete before proceeding. Each RNA has an sdp
      all_sdp_downloaded = False
      while not all_sdp_downloaded:
        all_sdp_downloaded = True
        for d in self.device_list:
          if not d.sdp_downloaded:
            all_sdp_downloaded = False
            print(f'Device {d.id} has not finished downloading sdp yet')
            break
          
      print('ALL SDPs downloaded!!!!!!!!!!!!!!!')

      # Start all the devices recording
      for d in self.device_list:
        success = d.start_recording(duration=self.duration,monitor=True)
        if not success:
          logging.error(f"Error: Recording device {d.id} at {d.ip} FAILED to start")
        else:
          logging.info(f"Recording device {d.id} at {d.ip} has started")

      self.is_recording = True
      self.update_gui_callback({
        'type': 'Recording started',
        'duration': self.duration,
        })

      # if enabled, turn on the dir monitor so we can see if the vlc processes are operating as they should
      if self.video_monitor_on:
        if not self.video_monitor:
          self.video_monitor = VidDirMonitor(
            dirpath=f'{self.sessionDirectory}',
            hz=1.0,
            logger=logging.info,
            update_callback=self.dir_monitor_update_callback)
        if not self.video_monitor.running:
          self.video_monitor.start() # this runs in its own thread

  def stop(self):
    
          
    logging.info('VidRecorder Stop!!!!!')
    for d in self.device_list:
      # d.quick_info()
      d.stop_recording()
      d.quick_info()
      # logging.info(f'subprocess pid: {d.video_subprocess.pid} -- dummy: {d.dummy} -- Terminating video_subprocess {d.vid_basename}')
      # print(d)
    # TODO: this needs to make one final check on filestats AFTER all vlc processes have terminated
    # TODO: before sending the stopped message to the gui
    self.is_recording = False
    self.update_gui_callback({
      'type': 'Recording stopped',
      'workstation_info': self.get_workstation_info(),
      'duration': self.duration,
      'abort': False,
      })
    
    
        
    if self.video_monitor and self.video_monitor.running:
      self.video_monitor.stop()
      self.video_monitor = None

  def get_workstation_info(self):
    w_info_list = []
    for d in self.device_list:
      w_info = d.get_workstation_info()
      w_info_list.append(w_info)
    return w_info_list

  def dir_monitor_update_callback(self,filestats):
    '''DirMonitor class will call this function after every directory check and pass the filestats'''

    if not filestats:
      print('filestats is empty in dir_monitor_update_callback')
      return
    
    workstation_info = self.get_workstation_info()

    for i,d in enumerate(self.device_list):
      for stats in filestats:
        # fullname = stats['fullname']
        # basename = os.path.basename(fullname)
        basename = stats['basename']

        # Do stuff based on file stats if you want to
        #
        # IMPORTANT NOTE: This function is being executed by the DirMonitor. Be careful with this
        # If you are running in another process you can't make any state changes, they don't share the same
        # memory space
        #
        if basename == d.vid_basename:
          d.handle_file_check(stats)
          workstation_info[i]['filestats'] = stats
          break
      
      # for w in workstation_info:
      #       w['is_recording'] = stats['size'] > 0
            
      if (not self.duration_thread and self.duration and self.duration > 0):
          for w in workstation_info:
            # Start duration timer here (in minutes)
            print(f'{w["id"]}: is_recording: {w["is_recording"]}')
            if w['is_recording']:
              self.duration_thread = threading.Timer(interval=self.duration*60, function=self.stop)
              self.duration_thread.start()
              break
        
      self.update_gui_callback({
        'type': 'Update',
        'workstation_info': workstation_info,
        'diskstats': shutil.disk_usage('/'),
        'diskstats_A': shutil.disk_usage(g.paths['hdd'][0]),
        'diskstats_B': shutil.disk_usage(g.paths['hdd'][1]),
        })

  def create_directory_structure(self,savedir,workstations,use_dev_dir=False):
        
        prev_dir_count = len(os.listdir(savedir))
        timestamp = f'{datetime.date.today().strftime("%Y-%b-%d")}_{time.strftime("%Hh%Mm%Ss", time.localtime())}'
        # if use_dev_dir:
        #     savedir = f'{savedir}/{(prev_dir_count+1):02}_{timestamp}'
        # else:
        #     savedir = f'{savedir}/{timestamp}'
        savedir = f'{savedir}/{(prev_dir_count+1):02}_{timestamp}'
        os.mkdir(savedir)
        for w in workstations:
            if (use_dev_dir):
                w['dir'] = savedir
            else:
                wid = f'{workstations.index(w) + 1:02}'
                w['dir'] = f'{savedir}/WS{wid}'
            if not os.path.isdir(w['dir']):
                os.mkdir(w['dir'])

        return (workstations,savedir)
