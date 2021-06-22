import sys
import math
import time
import threading
import logging
import modifiedTKV as tkv2
from vlc import State

from videoprops import get_video_properties

_isMacOS   = sys.platform.startswith('darwin')
_isWindows = sys.platform.startswith('win')
_isLinux   = sys.platform.startswith('linux')

format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO,
                    datefmt="%H:%M:%S")


class DevicePlayer():
    ''' Encapsulates all vlc operations for one playback operation in a frame
    '''
    def __init__(self, playback_gui, frame, controlsFrame, h, w, wsName=None, video=None, rootdir=None):
        self.playback_gui = playback_gui # TODO: REMOVE THIS HACK
        self.tkv = tkv2.Player(frame,controlsFrame,h,w,title=wsName,video=video)
        self.vlc_inspect_timer = None

        self.video = video
        self.rootdir = rootdir
        self.set_video(video,rootdir)
        
    def destroy(self):
        if self.vlc_inspect_timer:
            self.vlc_inspect_timer.cancel()
            self.vlc_inspect_timer = None
        self.tkv.player = None
        self.tkv = None

    def pause(self):
        self.tkv.player.pause()
        if self.vlc_inspect_timer:
            self.vlc_inspect_timer.cancel()
            self.vlc_inspect_timer = None
            
            
    def set_sync_wait_time(self, sync_wait_time):
        self.sync_wait_time_ms = sync_wait_time
        
    def _play_video(self):
        self.tkv.player.play()
        
    def play(self,time_offset_ms=0):
        print(f'Device: {self.tkv.title} -- sync_wait_time_ms: {self.sync_wait_time_ms}')
        # self.tkv.player.set_time(sync_time_ms)
        time_tosleep_ms = -1

        if time_offset_ms >=0 and self.sync_wait_time_ms > time_offset_ms:
            time_tosleep_ms = self.sync_wait_time_ms - time_offset_ms
            
        if time_tosleep_ms >= 0:
            wait_to_play_time = float(self.sync_wait_time_ms)/1000.0
        else:
            wait_to_play_time = 0
            self.tkv.player.set_time(int(time_offset_ms - self.sync_wait_time_ms))
            
        play_timer = threading.Timer(wait_to_play_time, self._play_video)
        play_timer.start()
        # print(f'BEFORE PLAY-- Device: {self.tkv.title} -- get_length(): {self.tkv.player.get_length()}')
        # self.tkv.player.play()
        # print(f'AFTER  PLAY-- Device: {self.tkv.title} -- get_length(): {self.tkv.player.get_length()}')
        # time.sleep(1)
        # print(f'AFTER  PLAY (1 second) -- Device: {self.tkv.title} -- get_length(): {self.tkv.player.get_length()}')
        if not self.vlc_inspect_timer:
            self.vlc_inspect_timer = threading.Timer(1.0, self.show_vlc_data)
            self.vlc_inspect_timer.start()
            
        # for player in self.tkvList:
        #     thread = threading.Thread(target=start_vlc_player, args=(player,))
        #     thread.start()
        #     self.playButton.config(text="Pause")
        
    # def start_vlc_player(player):
    #     player._Play()
    # print('Starting player embedded in frame')
    # print(player)

    def stop(self):
        self.tkv.player.stop()
        try:
            self.tkv.player.set_time(0)
        except e:
            print(e)
            
        if self.vlc_inspect_timer:
            self.vlc_inspect_timer.cancel()
            self.vlc_inspect_timer = None
            
    def mute(self):
        pass # TODO: Implement this
            
    def is_playing(self):
        return self.tkv.player.is_playing()
    
    def get_length(self):
        vid_props = get_video_properties(self.video)
        return float(vid_props['duration'])*1000 # in milliseconds
        # return self.tkv.player.get_length()
    
    def set_video(self,video,rootdir):
        self.video = video
        self.rootdir = rootdir
        self.start_time = DevicePlayer.get_start_time(self.rootdir)
        
        # Initialize player with new video
        m = self.tkv.Instance.media_new(video)
        self.tkv.player.set_media(m)
        
        # set the window id where to render VLC's video output
        h = self.tkv.videopanel.winfo_id()  # .winfo_visualid()?
        if _isWindows:
            self.tkv.player.set_hwnd(h)
        elif _isMacOS:
            # XXX 1) using the videopanel.winfo_id() handle
            # causes the video to play in the entire panel on
            # macOS, covering the buttons, sliders, etc.
            # XXX 2) .winfo_id() to return NSView on macOS?
            v = _GetNSView(h)
            if v:
                self.tkv.player.set_nsobject(v)
            else:
                self.tkv.player.set_xwindow(h)  # plays audio, no video
        else:
            self.tkv.player.set_xwindow(h)  # fails on Windows
        # FIXME: this should be made cross-platform
        

    # def jump_to_time(self, timestamp, delta_time=None):
    #     if not delta_time:
    #         # print(f'timestamp: {timestamp} -- type(timestamp): {type(timestamp)}')
    #         delta_time = time.mktime(timestamp) - time.mktime(DevicePlayer.get_start_time(self.rootdir))
    #         # print(f'delta_time: {delta_time} -- type(delta_time): {type(delta_time)}')

    #     # print(self.tkv.player.get_time())
    #     pct = delta_time * 1000 /  self.tkv.player.get_length()
    #     self.tkv.player.set_position(pct)
        
    def show_vlc_data(self):
        ''' Crude dump of all vlc knows about file it's playing
        '''
        t = self.tkv
        # t.timeVar.set(delta_time * 1000)
        # t.player.set_time(int(delta_time * 1000))
        
        
        print('------------------------------------------------------------------')
        print(f'Title: {t.title}')
        print(f'length: {t.player.get_length()}')
        print(f'movie_time(ms): {t.player.get_time()}')
        print(f'movie_position(pct between 0 and 1)): {t.player.get_position()}')
        print(f'movie_will_play: {t.player.will_play()}')
        print(f'get_rate: {t.player.get_rate()}')
        print(f'get_state: {t.player.get_state()}')
        # print(f'fps: {t.player.get_fps()} -- mspf: {(1000 // t.player.get_fps()) or 30}')
        if t.player.get_fps() > 0:
            print(f'fps: {t.player.get_fps()} -- mspf: {(1000 // t.player.get_fps()) or 30}')
        else:
            print(f'fps: {t.player.get_fps()}')
        
        
        # print(f'movie_chapter: {t.player.get_chapter()}')
        # print(f'movie_chapter_count: {t.player.get_chapter_count()}')
        # print(f'movie_title: {t.player.get_title()}')
        # print(f'chapter_count_for_title: {t.player.get_chapter_count_for_title(t.player.get_title())}')
        # print(f'has_vout: {t.player.has_vout()}')
        # print(f'is_seekable: {t.player.is_seekable()}')
        # print(f'can_pause: {t.player.can_pause()}')
        ####
        # print(f'program_scrambled: {t.player.program_scrambled()}')
        # print(f'next_frame: {t.player.next_frame()}')
        # print(f'video_get_scale: {t.player.video_get_scale()}')
        # print(f'video_get_aspect_ratio: {t.player.video_get_aspect_ratio()}')
        # print(f'video_get_spu: {t.player.video_get_spu()}')
        # print(f'video_get_spu_count: {t.player.video_get_spu_count()}')
        # print(f'video_get_spu_delay: {t.player.video_get_spu_delay()}')
        # print(f'video_get_crop_geometry: {t.player.video_get_crop_geometry()}')
        # print(f'video_get_teletext: {t.player.video_get_teletext()}')
        # print(f'video_get_track_count: {t.player.video_get_track_count()}')
        # print(f'video_get_track: {t.player.video_get_track()}')
        # print(f'video_get_marquee_int: {t.player.video_get_marquee_int()}')
        # print(f'video_get_marquee_string: {t.player.video_get_marquee_string()}')
        # print(f'video_get_logo_int: {t.player.video_get_logo_int()}')
        # print(f'video_get_adjust_int: {t.player.video_get_adjust_int()}')
        # print(f'video_get_adjust_float: {t.player.video_get_adjust_float()}')
        # print(f'audio_output_device_enum: {t.player.audio_output_device_enum()}')
        # print(f'audio_output_device_get: {t.player.audio_output_device_get()}')
        # print(f'audio_get_mute: {t.player.audio_get_mute()}')
        # print(f'audio_get_volume: {t.player.audio_get_volume()}')
        # print(f'audio_get_track_count: {t.player.audio_get_track_count()}')
        # print(f'audio_get_track: {t.player.audio_get_track()}')
        # print(f'audio_get_channel: {t.player.audio_get_channel()}')
        # print(f'audio_get_delay: {t.player.audio_get_delay()}')
        # print(f'get_role: {t.player.get_role()}')
        if t.player.get_state() == State.Ended: # enum in vlc.py
            print('Its ended!!!')
            self.playback_gui.stopAllControl()
            # self.stop()
        else:
            self.vlc_inspect_timer = threading.Timer(1.0, self.show_vlc_data)
            self.vlc_inspect_timer.daemon = True
            self.vlc_inspect_timer.start()

    @staticmethod
    def getdims(nVideos):
        '''Returns desired (rows,cols) and (width,height) of frames for number of movies in videoList'''
        if (nVideos == 1):
            return (1,1),(1300,720)
        elif (nVideos <= 2):
            return (1,2),(650,720)
        elif (nVideos <= 4):
            return (2,2),(650,360)
        elif (nVideos <= 6):
            return (2,3),(433,360)
        elif (nVideos <= 9):
            return (2,3),(433,240)
        elif (nVideos <= 12):
            return (3,4),(325,240)
    
    @staticmethod
    def get_start_time(directory):
        pieces = directory.split("/")
        for piece in pieces:
            try:
                # print(piece)
                piece = piece[piece.find('_')+1:]
                # print(piece)
                start_time = time.strptime(piece.strip(), "%Y-%b-%d_%Hh%Mm%Ss")
                # print(f'start_time: {start_time}')
                return start_time
            except:
                continue

if __name__ == '__main__':
    tile_dims,frame_dims = DevicePlayer.getdims(5)
    print(tile_dims)
    print(frame_dims)
    
    