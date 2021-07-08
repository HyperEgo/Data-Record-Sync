import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
import os
import datetime
import time
import vlc
import subprocess
import threading
import configparser
from DevicePlayer import DevicePlayer
from utils import utils

import sys
sys.path.append("../log_project")
import fake_log_generator
import log_parser

from os.path import basename, expanduser, isfile, join as joined
from pathlib import Path
from BookmarkHandler import BookmarkHandler

from global_vars import g


class PlaybackWindow_GUI:

    def __init__(self, root, config):

#Variables
        self.config = config
        self.my_log_player = None
        self.dir_filesLocation = os.path.expanduser('/mnt')
        self.displayDir = os.path.basename(os.path.normpath(self.dir_filesLocation))
        self.nodes = dict()
        self.bool_isDirSelected = BooleanVar(False)
        self.selectedDir = " "

    

#GUI Elements

        self.expandWidth = 1.4375
        self.expandHeight = 1.4861
        self.sizeFlag = config.get('dev_tools','devSize')
        print("Size flag = " + str(self.sizeFlag))

        self.playbackWindow = root
        self.playbackWindow.title('Workstation Playback - Version ' + config.get('version_info','versionNumber'))
        width=1600
        height=950
        # if(self.sizeFlag == '0'):
        #     width = 2300
        #     print( "w: " + str(width))
        #     height = 1412
        #     print( "h: " + str(height))
        screenwidth = self.playbackWindow.winfo_screenwidth()
        screenheight = self.playbackWindow.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.playbackWindow.geometry(alignstr)
        self.playbackWindow.resizable(width=False, height=False)
        self.playbackWindow.config(bg= "#383838")
        self.playbackWindow.protocol('WM_DELETE_WINDOW',self.on_close)

        button_OpenButton = tk.Button(self.playbackWindow)
        button_OpenButton["bg"] = "#efefef"
        ft = tkFont.Font(family='Verdana',size=10)
        button_OpenButton["font"] = ft
        button_OpenButton["fg"] = "#000000"
        button_OpenButton["justify"] = "center"
        button_OpenButton["text"] = "Open Files"
        button_OpenButton.place(x=20,y=10,width=100,height=30)
        button_OpenButton["command"] = self.choosePlaybackDirectory

        button_SendButton = tk.Button(self.playbackWindow)
        button_SendButton["bg"] = "#efefef"
        ft = tkFont.Font(family='Verdana',size=10)
        button_SendButton["font"] = ft
        button_SendButton["fg"] = "#000000"
        button_SendButton["justify"] = "center"
        button_SendButton["text"] = "Send to Player"
        button_SendButton.place(x=125,y=10,width=100,height=30)
        button_SendButton["command"] = self.sendToPlayback

        button_ClearMotherFrame = tk.Button(self.playbackWindow)
        button_ClearMotherFrame["text"]= "Clear"
        button_ClearMotherFrame.place(x=230,y=10,width=50,height=30)
        button_ClearMotherFrame["command"] = lambda: self.clearMother(self.motherFrame)


#Event Tree
        self.eventFrame = tk.Frame(self.playbackWindow,bg="dark gray")
        self.eventFrame.place(x=10,y=450,height=485,width=270)

        self.lowerFrame = tk.Frame(self.playbackWindow,bg="#383838")
        self.lowerFrame.place(x=290,y=770,height=175, width=1300)


#Directory Tree
        self.tree = ttk.Treeview(self.playbackWindow, selectmode="extended")
        ysb = ttk.Scrollbar(self.playbackWindow, orient='vertical', command=self.tree.yview)
        xsb = ttk.Scrollbar(self.playbackWindow, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscroll=ysb.set, xscroll=xsb.set)
        self.tree.heading('#0', text='', anchor='w')
        self.tree.place(x=10,y=45,width=250,height=390)
        ysb.place(x=260, y=45,width=20,height=390)

        self.tree.bind('<<TreeviewOpen>>', self.open_node)
        self.tree.bind('<<TreeviewSelect>>', self.onTreeSelect)

        self.motherFrame = tk.Frame(self.playbackWindow, bg="black")
        self.motherFrame.place(x=290,y=5,height=720,width=1300)

        self.playControl = tk.Frame(self.playbackWindow)
        self.playControl.place(x=290,y=725,height=40,width=1300)

        self.devicePlayers = []

        self.updateLabels()

#Controls

        self.playButton = ttk.Button(self.playControl, text="Play", command= self.playAllControl)
        self.stopButton = ttk.Button(self.playControl, text="Stop", command= self.stopAllControl)
        self.muteButton = ttk.Button(self.playControl, text="Mute", command= self.muteAllControl)
        self.playButton.place(x=0,y=0,width=65,height=40)
        self.stopButton.place(x=65,y=0,width=65,height=40)

        self.bookmarkButton = ttk.Button(self.playControl, text="Bookmark", command= self.newBookmark)
        self.bookmarkButton.place(x=130,y=0,width=100,height=40)

        self.volMuted = False
        self.volVar = tk.IntVar()
        self.volSlider = tk.Scale(self.playControl, variable=self.volVar,
                                  from_=0, to=100, orient=tk.HORIZONTAL,
                                  showvalue=0, label = 'Volume')
        self.volSlider.place(x=1200,y=0,width=100,height=40)



        timers = ttk.Frame(self.playControl)
        self.timeLabel = "00:00:00"
        self.timeVariable = tk.DoubleVar(self.playControl, value=0)
        self.timeSliderLast = 0
        self.timeSlider = tk.Scale(self.playControl, variable=self.timeVariable,
                                   from_=0, to=1000, orient=tk.HORIZONTAL,
                                   showvalue=0,label="-- / --", command=self.timeSlide)
        self.timeSlider.place(x=230,y=0,width=970,height=40)
        self.timeSliderUpdate = time.time()

        self.time_slider_update_timer = threading.Timer(1.0, self.time_slider_auto_updater)
        self.time_slider_update_timer.daemon = True
        self.time_slider_update_timer.start()

        self.label_timeOfRecord = tk.Label(self.lowerFrame,bg='white',foreground='black')
        self.label_timeOfRecord.place(x=0,y=0,height=45,width=230)
        self.label_timeOfRecord['text']= "Time of Record:  " + self.timeLabel


        self.testValue = " -?- "
        self.testLabel = tk.Label(self.lowerFrame,bg='yellow',foreground='black')
        #self.testLabel.place(x=55,y=55,height=45,width=1000)
        self.testLabel['text']= "test value:  " + self.testValue

#Functions


    def newBookmark(self):
        if(self.devicePlayers[0].is_playing):
            self.playAllControl()
        tagCreator = Toplevel(self.playControl)
        tagCreator.title("Custom Bookmark")
        width = 600
        height = 200
        screenwidth = self.playControl.winfo_screenwidth()
        screenheight = self.playControl.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        tagCreator.geometry(alignstr)
        tagCreator.resizable(width=False, height=False)
        tagCreator.config(bg= "#383838")

        tagString = tk.StringVar()
        tagEntry = tk.Entry(tagCreator)
        tagEntry["borderwidth"] = "1px"
        ft = tkFont.Font(family='Verdana',size=10)
        tagEntry["font"] = ft
        tagEntry["fg"] = "#333333"
        tagEntry["justify"] = "center"
        tagEntry["textvariable"] = tagString
        tagEntry.place(x=150,y=65,width=150,height=30)

        tagLabel= tk.Label(tagCreator, text="Tag: ")
        tagLabel["bg"] = "#383838"
        ft = tkFont.Font(family='Verdana',size=10)
        tagLabel["font"] = ft
        tagLabel["fg"] = "light gray"
        tagLabel["justify"] = "center"
        tagLabel.place(x=60,y=65)

        descString = tk.StringVar()
        descEntry = tk.Entry(tagCreator)
        descEntry["borderwidth"] = "1px"
        ft = tkFont.Font(family='Verdana',size=10)
        descEntry["font"] = ft
        descEntry["fg"] = "#333333"
        descEntry["justify"] = "center"
        descEntry["textvariable"] = descString
        descEntry.place(x=150,y=100,width=300,height=30)

        descLabel= tk.Label(tagCreator, text="Description: ")
        descLabel["bg"] = "#383838"
        ft = tkFont.Font(family='Verdana',size=10)
        descLabel["font"] = ft
        descLabel["fg"] = "light gray"
        descLabel["justify"] = "center"
        descLabel.place(x=60,y=100)

        timeLabel= tk.Label(tagCreator, text=self.getCurrentAbsTime())
        timeLabel["bg"] = "#383838"
        ft = tkFont.Font(family='Verdana',size=15)
        timeLabel["font"] = ft
        timeLabel["fg"] = "light gray"
        timeLabel["justify"] = "center"
        timeLabel.place(x=150,y=20)
        confirmButton = tk.Button(tagCreator,text= "OK",command= lambda: self.setBookmark(tagCreator,tagEntry, descEntry))
        confirmButton.place(x=150,y=135,width=65,height=30)

    def setBookmark(self,window,tagBox,descBox):

        ttime = self.getCurrentAbsTime()
        bookmarker = BookmarkHandler(self.dir_filesLocation,ttime)
        bookmarker.createBookmark(tagBox,descBox)
        self.playAllControl()
        threading.Thread(target=self.my_log_player.refresh_bookmarks).start()
        window.destroy()

    def getCurrentAbsTime(self):
        current_position = self.devicePlayers[0].tkv.player.get_position()
        tStamp = time.localtime(time.mktime(DevicePlayer.get_start_time(self.dir_filesLocation)) + self.devicePlayers[0].tkv.player.get_time() / 1000.0)
        thisTime = time.strftime("%d %B %Y %H:%M:%S", tStamp)
        return thisTime

    def timetranslator(self,sec):
        return utils.timetranslator(sec)


    def get_longest_video(self):
        max_player = None
        for current_player in self.devicePlayers:
            if max_player is None:
                max_player = current_player
            elif current_player.tkv.player.get_length() > max_player.tkv.player.get_length():
                max_player = current_player
        return max_player


    def time_slider_auto_updater(self):
        if len(self.devicePlayers) > 0:
            try:
                current_position = self.get_longest_video().tkv.player.get_position()
                self.timeVariable.set(current_position * 1000.0)

                current_time = self.get_longest_video().tkv.player.get_time() * 1e-3  # to seconds
                media_duration = self.get_longest_video().tkv.player.get_length() * 1e-3 # to seconds
                labelString = f'{self.timetranslator(current_time)} / {self.timetranslator(media_duration)}'
                self.timeSlider.configure(label= labelString)
                timestamp = time.localtime(time.mktime(DevicePlayer.get_start_time(self.dir_filesLocation)) + self.get_longest_video().tkv.player.get_time() / 1000.0)
                myTime = time.strftime("%H:%M:%S", timestamp)
                self.label_timeOfRecord.configure(text= "Time of Record: " + myTime)
            except:
                pass

        self.time_slider_update_timer = threading.Timer(1.0, self.time_slider_auto_updater)
        self.time_slider_update_timer.daemon = True
        self.time_slider_update_timer.start()



    def timeSlide(self,value):
        if(len(self.devicePlayers) > 0):
            start_time = time.mktime(DevicePlayer.get_start_time(self.dir_filesLocation))
            total_size = self.get_longest_video().tkv.player.get_length() # ms
            ms_to_jump_to = self.timeVariable.get() * total_size / 1000.0
            destination_time = time.localtime(start_time + ms_to_jump_to / 1000.0)
            threading.Thread(target=self.my_log_player._jump_to_time,args=(destination_time,)).start()

    def jump_to_time(self, timestamp):
        ms_offset = (time.mktime(timestamp) - time.mktime(DevicePlayer.get_start_time(self.dir_filesLocation))) * 1000
        for d in self.devicePlayers:
            d.play(time_offset_ms=ms_offset)

    def clickedVideoPanel(self, event):
        self.playAllControl()

    def playAllControl(self):
        ''' Called when Play button is pushed (NOT Send To Playback) '''
        for d in self.devicePlayers:
            if d.is_playing():
                d.pause()
                self.playButton.config(text="Play")
            else:
                d.play()
                self.playButton.config(text="Pause")
                if self.my_log_player is None:
                    try:
                        self.my_log_player = log_parser.LogPlayer(master=self.eventFrame, dir_path=self.get_logs_dir() + "/", start_time=DevicePlayer.get_start_time(self.dir_filesLocation), playback_gui=self)
                        self.my_log_player.pause_play()
                    except:
                        print("There is no logs folder in selected directory.")

        self.my_log_player.pause_play()

    def stopAllControl(self):
        for d in self.devicePlayers:
            d.stop()
        self.playButton.config(text="Play")
        # self.my_log_player.log_timer.cancel()
        # self.my_log_player.clock_timer.cancel()
        # self.my_log_player.log_timer = None
        # self.my_log_player.clock_timer = None
        if self.my_log_player:
            self.my_log_player.destroy()
            self.my_log_player = None

    def muteAllControl(self):
        for d in self.devicePlayers:
            d.mute()

    def clearMother(self,frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def choosePlaybackDirectory(self):

        selection = filedialog.askdirectory(title= 'Select Directory', initialdir=self.dir_filesLocation)
        if(len(selection) <= 1):
            selection = self.dir_filesLocation
        else:
            self.dir_filesLocation = selection
        # print("Path: " + str(selection))
        self.tree.delete(*self.tree.get_children())

        self.updateLabels()

    def insert_node(self, parent, text, abspath):
        node = self.tree.insert(parent, 'end', text=text, open=False)
        if os.path.isdir(abspath):
            self.nodes[node] = abspath
            self.tree.insert(node, 'end')

    def open_node(self, event):
        node = self.tree.focus()
        abspath = self.nodes.pop(node, None)
        if abspath:
            self.tree.delete(self.tree.get_children(node))
            pathlist = os.listdir(abspath)
            pathlist.sort()
            for p in pathlist:
                self.insert_node(node, p, os.path.join(abspath, p))

    def getTreeSelection(self):
        fullPath = []
        selection = self.tree.selection()
        for item in selection:
            # itemText = self.tree.item(item, "text")
            # fullPath.append(self.dir_filesLocation + "/" + itemText)
            fullPath.append(self.get_full_path(item))
        return fullPath

    def get_full_path(self, item):
        if self.tree.parent(item) == "":
            return self.tree.item(item, "text")
        else:
            return self.get_full_path(self.tree.parent(item)) + "/" + self.tree.item(item, "text")


    def onTreeSelect(self,event):
        self.bool_isDirSelected = False # TODO: Implement this
        # fullpath = getTreeSelection()
        # self.bool_isDirSelected = os.path.isdir(fullPath)
        # self.selectedDir = itemText
        # print("Selected Item:" + itemText)
        # print ("Full path of selected: " + str(fullPath))
        # print("Is this a directory? " + str(os.path.isdir(fullPath)))

    def get_logs_item(self):
        current_item = self.tree.parent(self.tree.focus())
        for child in self.tree.get_children(current_item):
            if self.tree.item(child, "text").find("logs") != -1:
                return child

    def get_logs_dir(self):
        return self.get_full_path(self.get_logs_item())

    def sendToPlayback(self):
        if self.my_log_player is not None:
            self.my_log_player.destroy()
        try:
            self.my_log_player = log_parser.LogPlayer(master=self.eventFrame, dir_path=self.get_logs_dir() + "/", start_time=DevicePlayer.get_start_time(self.dir_filesLocation), playback_gui=self)
        except:
            print("There is no logs folder in selected directory.")

        # Cleanup old device player instances
        for d in self.devicePlayers:
            d.destroy()
        self.devicePlayers = []


        if(self.bool_isDirSelected): # TODO: Implement this
            if(self.selectedDir[0] == 'W' and self.selectedDir[1] == 'S'):
                pass
                #TODO: Create file directory parser to check for various file types so they can be dealt with appropriately.
                #TODO: Play inside application
                #TODO: Send any .txt files to the log parser
                # self.my_log_player = log_parser.LogPlayer(master=self.eventFrame, dir_path=self.getTreeSelection())
                # self.my_log_player = log_parser.LogPlayer(master=self.eventFrame, path=self.selectedDir + "/logs")
            else:
                message="Directory confirmed, but incorrect directory."
                self.noGoodForPlayback(message)

        elif(not self.bool_isDirSelected):
            # itemText = self.tree.item(self.tree.selection(), "text")
            # fullPath = self.dir_filesLocation + "/" + itemText
            vidList = []
            allpaths = self.getTreeSelection()

            for f in allpaths:
                name, extension = os.path.splitext(f)
                if(extension.lower() == ".mp4"):
                    path_to_vid = f
                    vidList.append(path_to_vid)
                else:
                    message="Incorrect file type."
                    self.noGoodForPlayback(message)

        else:
            message="Selection is unknown. Select a WS# directory or an MP4 file."
            self.noGoodForPlayback(message)

        # Setup frames for playing the videos
        if(len(vidList) > 0):
            self.play_video_list(vidList)

    def updateLabels(self):
        self.displayDir = os.path.basename(os.path.normpath(self.dir_filesLocation))
        self.tree.heading('#0', text=self.displayDir, anchor='w')

        abspath = os.path.abspath(self.dir_filesLocation)
        self.insert_node('', abspath, abspath)
        self.tree.bind('<<TreeviewOpen>>', self.open_node)

    def noGoodForPlayback(self,message):
        messagebox.showinfo('Try Again', message, parent=self.playbackWindow)

    def getdims(self,videoList):
        '''Returns desired (rows,cols) and (width,height) of frames for number of movies in videoList'''
        nVideos = len(videoList)
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

    def play_video_list(self,videoList):
        '''Creates and tiles frames for each video'''

        # Delete old frames
        for widget in self.motherFrame.winfo_children():
            widget.destroy()

        # Get desired dimensions to divide the mother frame into multiple frames for each video
        tile_dims,frame_dims = DevicePlayer.getdims(len(videoList))

        # For each video, create a frame/label and add a vlc player
        xPos = yPos = 0
        w,h = frame_dims
        rows,cols = tile_dims
        for n, v in enumerate(sorted(videoList)):
            fr = tk.Frame(self.motherFrame)
            wsName = os.path.basename(v)
            xPos = w * (n%cols)
            yPos = h * int(n/cols)
            fr.place(x=xPos,y=yPos,width=w,height=h)
            label = tk.Label(self.motherFrame,text=wsName)
            label.place(x=xPos,y=yPos,height=30,width=200)
            player = DevicePlayer(self,fr,self.playControl,h,w,wsName=wsName,video=v,rootdir=self.dir_filesLocation)
            self.devicePlayers.append(player)

        # Calculate time to wait for each device to synch with the longest vid recorded

        all_len = []
        max_len = 0
        for d in self.devicePlayers:
            vid_len = d.get_length()
            all_len.append(vid_len)
            if vid_len > max_len:
                max_len = vid_len

        print(f'max_len: {max_len}')
        print(f'all_len: {all_len}')

        # for i,d in enumerate(self.devicePlayers):
        #     sync_time_ms = (max_len - all_len[i])
        #     print(f'sync_time_ms: {sync_time_ms}')

        # Play the videos
        for i,d in enumerate(self.devicePlayers):
            sync_time_ms = (max_len - all_len[i])
            d.set_sync_wait_time(sync_time_ms)
            d.play()

        self.playButton.config(text="Pause")
        
    def on_close(self):
        print('Does this work????')
        self.playbackWindow.destroy()

def start_vlc_player(player):
    player._Play()
    print('Starting player embedded in frame')
    # print(player)




# def playback_vid(path_to_vid):
#     thread = threading.Thread(target=thread_func, args=(path_to_vid,))
#     thread.start()

# def thread_func(path_to_vid):
#     vlcapp = '/usr/bin/vlc'
#     subprocess.run([vlcapp, '--width', '600', '--height', '300', path_to_vid])


# Main
if __name__ == "__main__":
    root = tk.Tk()
    app = PlaybackWindow_GUI(root)
    root.mainloop()