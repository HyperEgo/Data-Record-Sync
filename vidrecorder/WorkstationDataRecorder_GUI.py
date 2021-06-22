import tkinter as tk
import tkinter.font as tkFont
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
import os
import datetime
import time
from VidRecorder import VidRecorder
from PlaybackWindow_GUI import PlaybackWindow_GUI as playbackGUI
import modifiedTKV as tkVid
import Stopwatch
import configparser
import shutil
from global_vars import g
import sys
sys.path.append("../log_project")
import fake_log_generator
import log_parser

from utils import utils

class WorkstationDataRecorder_GUI:
    def __init__(self, root, config):

        self.root = root
        self.config = config
        self.expandWidth = 1.4375
        self.expandHeight = 1.4861
        self.sizeFlag = config.get('dev_tools','devSize')

        curdir = os.getcwd()
        # viddir = curdir + '/prac/vids'
        self.parentDirectory = StringVar()
        self.recorder = None

        self.playWin_toplevel = None
        self.instructionWindow = None
        # timestamps for generating test logs
        self.begin = None
        self.end = None

        self.bool_IsRecording = BooleanVar()
        self.bool_IsRecording = False

        self.bool_useDuration = BooleanVar()
        self.duration = ""

        self.bool_WS1 = tk.BooleanVar()
        self.bool_WS2 = tk.BooleanVar()
        self.bool_WS3 = tk.BooleanVar()
        self.bool_WS4 = tk.BooleanVar()
        self.bool_WS5 = tk.BooleanVar()
        self.bool_WS6 = tk.BooleanVar()
        self.bool_WS7 = tk.BooleanVar()
        self.bool_WS8 = tk.BooleanVar()
        self.bool_WS9 = tk.BooleanVar()
        self.bool_WS10 = tk.BooleanVar()
        self.bool_WS11 = tk.BooleanVar()
        self.bool_WS12 = tk.BooleanVar()

        self.source1 = tk.StringVar()
        self.source2 = tk.StringVar()
        self.source3 = tk.StringVar()
        self.source4 = tk.StringVar()
        self.source5 = tk.StringVar()
        self.source6 = tk.StringVar()
        self.source7 = tk.StringVar()
        self.source8 = tk.StringVar()
        self.source9 = tk.StringVar()
        self.source10 = tk.StringVar()
        self.source11 = tk.StringVar()
        self.source12 = tk.StringVar()

        self.label_ws1_recordingStatus = tk.Label(root)
        self.label_ws2_recordingStatus = tk.Label(root)
        self.label_ws3_recordingStatus = tk.Label(root)
        self.label_ws4_recordingStatus = tk.Label(root)
        self.label_ws5_recordingStatus = tk.Label(root)
        self.label_ws6_recordingStatus = tk.Label(root)
        self.label_ws7_recordingStatus = tk.Label(root)
        self.label_ws8_recordingStatus = tk.Label(root)
        self.label_ws9_recordingStatus = tk.Label(root)
        self.label_ws10_recordingStatus = tk.Label(root)
        self.label_ws11_recordingStatus = tk.Label(root)
        self.label_ws12_recordingStatus = tk.Label(root)

        self.addressBoxLocation_Y = 270
        self.numWorkstations = 1
        self.currentWorkstation = 1

        self.initSources()
        self.makeLists()
        self.populateWindow()
        self.toggleEntry_Duration()

#Functions
    def createStatusLabels(self):
        xPos = 500
        yPos = 275
        for lbl in self.statusLabelList:
            lbl["justify"] = "center"
            lbl["fg"] = "light gray"
            lbl["background"] = "#383838"
            lbl["font"] = tkFont.Font(family='Verdana',size=10)
            lbl.place(x=xPos,y=yPos)#,width=70,height=30)
            yPos += 35

    def updateStatusLabels(self,workstation_info,record_state=None):
        for w in workstation_info:
            wid = w['id']
            filestats = w['filestats']
            lbl_idx = wid-1
            if lbl_idx >= 0 and lbl_idx < len(self.statusLabelList):
                lbl = self.statusLabelList[lbl_idx]
                if record_state == 'started' and filestats == None:
                    text = "Pending..."
                elif record_state == 'sdp_download' and filestats == None and w['sdp_downloaded'] == False:
                    text = f'Workstation SDP download failed.'
                elif record_state == 'sdp_download' and filestats == None and w['sdp_downloaded'] == True:
                    text = f'Workstation SDP download success.'
                # elif record_state == 'started' and filestats and filestats['size'] == 0: # w['filestats']['size']
                #     text = f"Establishing connection. Please wait..."
                # elif record_state == 'started':
                #     text = f"Recording... | File size: {utils.bytesto(filestats['size'], 'mb'):.2f} MB"
                #     self.stopWatch.Start()
                elif record_state == 'started' and not w['is_recording']: # w['filestats']['size']
                    text = f"Establishing connection. Please wait..."
                elif record_state == 'started' and w['is_recording']:
                    text = f"Recording... | File size: {utils.bytesto(filestats['size'], 'mb'):.2f} MB"
                    self.stopWatch.Start()
                elif record_state == 'stopped':
                    text = f"Stopped | File size: {utils.bytesto(filestats['size'], 'mb'):.2f} MB"
                    # self.stopWatch.Stop()
                else:
                    text = 'ERROR: Unknown recording state in gui'

                lbl.configure(text = text)

    def openPlayback(self, _class):
        if(self.playWin_toplevel is None):
            self.root.iconify()
            self.playWin_toplevel = tk.Toplevel(self.root)
            self.playWin_toplevel.protocol('WM_DELETE_WINDOW',self.onPlaybackClose)
            _class(self.playWin_toplevel,self.config)
            print('End openPlayback')

    def onPlaybackClose(self):
        self.playWin_toplevel.destroy()
        self.playWin_toplevel = None

    def openTkVid(self):
        self.root.iconify()
        tkVid(self.new)

    def clearAllSources(self):
        for src in self.sourceEntryList:
                if(len(src.get()) > 0):
                    src.delete(0,'end')
        self.bool_checkedAllWorkstations.set(False)
        self.bool_useDuration.set(False)
        self.entry_duration.delete(0,'end')
        self.entry_duration.config(state=DISABLED)
        self.stopWatch.Reset()
        for chk in self.workstationBoolList:
            chk.set(False)
        for chk in self.chkBoxList:
            chk['state'] = NORMAL

        # g.paths['viddir'] = g.config.get('dcp_config','defaultSaveLocation')
        # self.entry_SaveDir["state"] = NORMAL
        # self.entry_SaveDir.insert(0,g.paths['viddir'])
        # self.entry_SaveDir["state"] = DISABLED

        for lbl in self.statusLabelList:
            lbl.configure(text=' ')

    def toggleRecord(self):
        for src in self.sourceInputList:
            text = src.get()
            if(len(text) > 0):
                if(not self.recorder or self.recorder.is_recording == False):
                    self.startRecordAll()
                else:
                    self.stopRecordAll()
                break

    def get_selected_workstations(self,savedir):
        workstations = []
        for src in self.sourceInputList:
            ip = src.get()
            idx = self.sourceInputList.index(src)
            if(self.workstationBoolList[idx].get() == True):
                # TODO: wsDirectory = savedir + "/" + "WS_" + text
                # wsDirectory = savedir
                workstations.append(
                    {
                        "id": int(ip[-2:]) % 70,
                        "ip": ip,
                        "restart_interval": 5,
                        # "dir": wsDirectory
                    }
                )

        return workstations


    def startRecordAll(self):
        try:
            for chk in self.chkBoxList:
                chk["state"]= DISABLED

            self.begin = time.localtime()

            # Get list of selected workstations
            workstations = self.get_selected_workstations(savedir=self.parentDirectory)

            # Create directory structure associated with workstations
            # workstations = self.create_directory_structure(self.parentDirectory,workstations)

            # Get duration from gui
            self.duration = 0
            if(self.bool_useDuration.get() == True):
                self.duration = float(self.entry_duration.get())

            print(self.recorder)
            if (self.recorder is None):
                use_dev_dir  = self.config.get('dev_tools','devDirectory') == "1"
                self.recorder = VidRecorder(workstations, savedir=self.parentDirectory, sdpdir=g.paths['sdpdir'],
                                            duration=self.duration, update_callback=self.on_vidrecorder_update, use_dev_dir=use_dev_dir)

            print(self.recorder)
            if not self.recorder.is_recording:
                self.recorder.start()
                # self.stopWatch.Reset()
                # self.stopWatch.Start()
                self.bool_IsRecording = True
                self.button_Record["text"] = "Stop"
            else:
                self.stopWatch.Reset()
                #self.stopWatch.Start()
                self.button_Record["text"] = "Stop"
        except:
            print("Unable to begin recording. Start Recording command failed.")
            messagebox.showinfo('Start Command Failure', "Unable to begin recording.", parent=self.root)
            self.clearAllSources()

    def stopRecordAll(self):

        # Stop the vidrecorder
        if (self.recorder and self.recorder.is_recording):
            print(f'duration: {self.recorder.duration}')
            self.recorder.stop()

        #Delete session directory if nothing was recorded.
        # if(os.listdir(self.recorder.sessionDirectory) == []):
        #     os.rmdir(self.recorder.sessionDirectory)

        if self.recorder:
            self.end = time.localtime()
            if((self.config.get('dev_tools','devLogCreator')) == '1'):
                fake_log_generator.generate_log(self.begin, self.end, dir_path=self.recorder.sessionDirectory + "/logs/")
            # self.stopWatch.Stop()
            self.bool_IsRecording = False
            # self.button_Record["text"] = "Record"

        self.recorder = None

    def OnStopRecordingHandler(self,info=None):
        # update gui with info if needed
        pass

    def on_vidrecorder_update(self,update):
        if (update['type'] == 'Update'):
            workstation_info = update['workstation_info']
            
            self.updateStatusLabels(workstation_info,record_state='started')

            hdd = update['diskstats']
            hdd_1 = update['diskstats_A']
            hdd_2 = update['diskstats_B']

            # print(f'Total: {hdd.total / 2**30} GiB')
            # print(f'Used: {hdd.used / 2**30} GiB')
            # print(f'Free: {hdd.free / 2**30} GiB')
            self.label_HDD_Space["text"]= f"{(hdd_1.free / 2**30):.2f} GB"
            self.label_HDD_Space_2["text"]= f"{(hdd_2.free / 2**30):.2f} GB"

            if ((hdd_1.free / 2**30)) < 350.00:
                self.label_HDD_Space["fg"] = "red"
                if g.paths['viddir'] == "/mnt/dd1":
                    self.label_HDD_Message_A['text']= "Limit Reached - Overwriting Disk A"
            elif ((hdd_1.free / 2**30)) < 450.00:
                self.label_HDD_Space["fg"] = "#e0d900"
            if ((hdd_2.free / 2**30)) < 350.00:
                self.label_HDD_Space_2["fg"] = "red"
                if g.paths['viddir'] == "/mnt/dd2":
                    self.label_HDD_Message_B['text']= "Limit Reached - Overwriting Disk B"
            elif ((hdd_2.free / 2**30)) < 450.00:
                self.label_HDD_Space_2["fg"] = "#e0d900"

        elif(update['type'] == 'Recording started'):
            print('---------------------------------')
            print('RECORDING STARTED -- update to gui here')
            print('---------------------------------')
            
            # Update stop watch
            self.stopWatch.Reset()
            
        elif(update['type'] == 'Recording stopped'):
            print('---------------------------------')
            print('RECORDING STOPPED -- update to gui here')
            print('---------------------------------')
            duration = update['duration']
            workstation_info = update['workstation_info']

            # Update checkboxes
            for chk in self.chkBoxList:
                chk["state"]= NORMAL

            # Update start/stop button
            self.button_Record["text"] = "Record"

            # Update status labels
            self.updateStatusLabels(workstation_info,record_state='stopped')
            
            # Update stop watch
            self.stopWatch.Stop()
            
            self.stopRecordAll()



        elif(update['type'] == 'SDP Download Status'):
            self.updateStatusLabels(update['workstation_info'],record_state='sdp_download')

    def menuNewRecording(self):
        self.clearAllSources()
        if((self.config.get('dev_tools','devEditableSaveLocation')) == '1'):
            self.chooseDirectory()

    def chooseDirectory(self):
        '''Browse button that allows you to change viddir save location'''

        initial_dir = []
        config_vid_dir = g.paths['viddir']

        if os.path.exists(config_vid_dir) and os.path.isdir(config_vid_dir):
            initial_dir = config_vid_dir
        else:
            initial_dir = os.getcwd()

        selection = filedialog.askdirectory(title= 'Select Destination',
                                            initialdir=initial_dir)
        if not selection:
            print('Cancel was pressed -- aborting selection')
            return

        self.parentDirectory = selection
        g.paths['viddir'] = selection

        os.chdir(self.parentDirectory)
        self.entry_SaveDir.config(state= NORMAL)
        self.entry_SaveDir.delete(0,'end')
        self.entry_SaveDir.insert(0,os.getcwd())
        self.entry_SaveDir.xview_moveto(1)
        self.entry_SaveDir.config(state= DISABLED)

    def checkAllWorkstations(self):
        flag = False
        for chk in self.workstationBoolList:
            idx = self.workstationBoolList.index(chk)
            chk.set(self.bool_checkedAllWorkstations.get())

    def closeInstructions(self):
        self.instructionWindow.destroy()
        self.instructionWindow = None

    def toggleEntry_Duration(self):
        if(self.entry_duration["state"] == NORMAL):
            self.entry_duration.config(state=DISABLED)
        else:
            self.entry_duration.config(state=NORMAL)

    def openInstructions(self):
        if(self.instructionWindow is None):
            self.instructionWindow = Toplevel(self.root)
            self.instructionWindow.protocol('WM_DELETE_WINDOW',self.closeInstructions)
            self.instructionWindow.title("Instructions")
            width=600
            height=600
            screenwidth = self.root.winfo_screenwidth()
            screenheight = self.root.winfo_screenheight()
            alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
            self.instructionWindow.geometry(alignstr)
            self.instructionWindow.resizable(width=False, height=False)
            self.instructionWindow.config(bg= "#383838")

            label_Title=tk.Label(self.instructionWindow)
            label_Title["anchor"] = "center"
            label_Title["bg"] = "#383838"
            ft = tkFont.Font(family='Verdana',size=18)
            label_Title["font"] = ft
            label_Title["fg"] = "#69a078"
            label_Title["justify"] = "center"
            label_Title["text"] = "RECORDING INSTRUCTIONS"
            label_Title.place(x=100,y=5,width=400,height=75)

            label_Step1=tk.Label(self.instructionWindow)
            label_Step1["anchor"] = "w"
            label_Step1["bg"] = "#383838"
            ft = tkFont.Font(family='Verdana',size=8)
            label_Step1["font"] = ft
            label_Step1["fg"] = "light gray"
            label_Step1["justify"] = "left"
            label_Step1["text"] = "1. The storage location is set in the configuration file." #If permission to edit it is enabled, \n\n    click the \'Browse\' button to set the saved file directory, or click File->New Recording. \n\n    Note: If \'New Recording\' is selected via the file menu, all previously filled fields will be cleared."
            label_Step1.place(x=10,y=85,width=550,height=70)

            label_Step2=tk.Label(self.instructionWindow)
            label_Step2["anchor"] = "w"
            label_Step2["bg"] = "#383838"
            ft = tkFont.Font(family='Verdana',size=8)
            label_Step2["font"] = ft
            label_Step2["fg"] = "light gray"
            label_Step2["justify"] = "left"
            label_Step2["text"] = "2. Check the box for each workstation to be recorded, or check the \'ALL\' box to select them all."
            label_Step2.place(x=10,y=145,width=550,height=50)

            label_Step3=tk.Label(self.instructionWindow)
            label_Step3["anchor"] = "w"
            label_Step3["bg"] = "#383838"
            ft = tkFont.Font(family='Verdana',size=8)
            label_Step3["font"] = ft
            label_Step3["fg"] = "light gray"
            label_Step3["justify"] = "left"
            label_Step3["text"] = "3. Press the \'Record\' button to start recording. It will then change into the \'Stop\' button, which \n\n    can be pressed to end the recording session."
            #label_Step3["text"] = "3. Check the boxes for audio and data as desired for each \n\n    workstation, or check the box labeled \'ALL\' to capture all workstation audio or data." + '\u0336'
            label_Step3.place(x=10,y=205,width=550,height=50)

            label_Step4=tk.Label(self.instructionWindow)
            label_Step4["anchor"] = "w"
            label_Step4["bg"] = "#383838"
            ft = tkFont.Font(family='Verdana',size=8)
            label_Step4["font"] = ft
            label_Step4["fg"] = "light gray"
            label_Step4["justify"] = "left"
            label_Step4["text"] = "4. If desired, check the \'DURATION\' box and enter a numerical time in minutes. The recording \n\n    will stop after recording that amount of time."
            label_Step4.place(x=10,y=265,width=550,height=50)

            # label_pTitle=tk.Label(self.instructionWindow)
            # label_pTitle["anchor"] = "center"
            # label_pTitle["bg"] = "#383838"
            # ft = tkFont.Font(family='Verdana',size=18)
            # label_pTitle["font"] = ft
            # label_pTitle["fg"] = "#69a078"
            # label_pTitle["justify"] = "center"
            # label_pTitle["text"] = "PLAYBACK INSTRUCTIONS"
            # label_pTitle.place(x=100,y=340,width=400,height=75)
    def makeLists(self):
        self.sourceLabelList = [self.label_source1,
                                self.label_source2,
                                self.label_source3,
                                self.label_source4,
                                self.label_source5,
                                self.label_source6,
                                self.label_source7,
                                self.label_source8,
                                self.label_source9,
                                self.label_source10,
                                self.label_source11,
                                self.label_source12]

        self.sourceInputList = [self.source1,
                                self.source2,
                                self.source3,
                                self.source4,
                                self.source5,
                                self.source6,
                                self.source7,
                                self.source8,
                                self.source9,
                                self.source10,
                                self.source11,
                                self.source12]

        self.sourceEntryList = [self.sourceEntry1,
                                self.sourceEntry2,
                                self.sourceEntry3,
                                self.sourceEntry4,
                                self.sourceEntry5,
                                self.sourceEntry6,
                                self.sourceEntry7,
                                self.sourceEntry8,
                                self.sourceEntry9,
                                self.sourceEntry10,
                                self.sourceEntry11,
                                self.sourceEntry12]

        self.workstationBoolList = [self.bool_WS1,
                                    self.bool_WS2,
                                    self.bool_WS3,
                                    self.bool_WS4,
                                    self.bool_WS5,
                                    self.bool_WS6,
                                    self.bool_WS7,
                                    self.bool_WS8,
                                    self.bool_WS9,
                                    self.bool_WS10,
                                    self.bool_WS11,
                                    self.bool_WS12]

        self.chkBoxList = [self.chk_WS1,
                           self.chk_WS2,
                           self.chk_WS3,
                           self.chk_WS4,
                           self.chk_WS5,
                           self.chk_WS6,
                           self.chk_WS7,
                           self.chk_WS8,
                           self.chk_WS9,
                           self.chk_WS10,
                           self.chk_WS11,
                           self.chk_WS12]

        self.statusLabelList = [self.label_ws1_recordingStatus,
                                self.label_ws2_recordingStatus,
                                self.label_ws3_recordingStatus,
                                self.label_ws4_recordingStatus,
                                self.label_ws5_recordingStatus,
                                self.label_ws6_recordingStatus,
                                self.label_ws7_recordingStatus,
                                self.label_ws8_recordingStatus,
                                self.label_ws9_recordingStatus,
                                self.label_ws10_recordingStatus,
                                self.label_ws11_recordingStatus,
                                self.label_ws12_recordingStatus]
    def initSources(self):
        self.label_source1=tk.Label(self.root)
        self.label_source1.place(x=100,y=270,width=121,height=30)
        self.sourceEntry1=tk.Entry(self.root)
        self.sourceEntry1.place(x=220,y=270,width=200,height=30)
        self.chk_WS1=tk.Checkbutton(self.root)
        self.chk_WS1.place(x=425,y=270,width=70,height=30)

        self.label_source2=tk.Label(self.root)
        self.label_source2.place(x=100,y=305,width=121,height=30)
        self.sourceEntry2=tk.Entry(self.root)
        self.sourceEntry2.place(x=220,y=305,width=200,height=30)
        self.chk_WS2=tk.Checkbutton(self.root)
        self.chk_WS2.place(x=425,y=305,width=70,height=30)

        self.label_source3=tk.Label(self.root)
        self.label_source3.place(x=100,y=340,width=121,height=30)
        self.sourceEntry3=tk.Entry(self.root)
        self.sourceEntry3.place(x=220,y=340,width=200,height=30)
        self.chk_WS3=tk.Checkbutton(self.root)
        self.chk_WS3.place(x=425,y=340,width=70,height=30)

        self.label_source4=tk.Label(self.root)
        self.label_source4.place(x=100,y=375,width=121,height=30)
        self.sourceEntry4=tk.Entry(self.root)
        self.sourceEntry4.place(x=220,y=375,width=200,height=30)
        self.chk_WS4=tk.Checkbutton(self.root)
        self.chk_WS4.place(x=425,y=375,width=70,height=30)

        self.label_source5=tk.Label(self.root)
        self.label_source5.place(x=100,y=410,width=121,height=30)
        self.sourceEntry5=tk.Entry(self.root)
        self.sourceEntry5.place(x=220,y=410,width=200,height=30)
        self.chk_WS5=tk.Checkbutton(self.root)
        self.chk_WS5.place(x=425,y=410,width=70,height=30)

        self.label_source6=tk.Label(self.root)
        self.label_source6.place(x=100,y=445,width=121,height=30)
        self.sourceEntry6=tk.Entry(self.root)
        self.sourceEntry6.place(x=220,y=445,width=200,height=30)
        self.chk_WS6=tk.Checkbutton(self.root)
        self.chk_WS6.place(x=425,y=445,width=70,height=30)

        self.label_source7=tk.Label(self.root)
        self.label_source7.place(x=100,y=480,width=121,height=30)
        self.sourceEntry7=tk.Entry(self.root)
        self.sourceEntry7.place(x=220,y=480,width=200,height=30)
        self.chk_WS7=tk.Checkbutton(self.root)
        self.chk_WS7.place(x=425,y=480,width=70,height=30)

        self.label_source8=tk.Label(self.root)
        self.label_source8.place(x=100,y=515,width=121,height=30)
        self.sourceEntry8=tk.Entry(self.root)
        self.sourceEntry8.place(x=220,y=515,width=200,height=30)
        self.chk_WS8=tk.Checkbutton(self.root)
        self.chk_WS8.place(x=425,y=515,width=70,height=30)

        self.label_source9=tk.Label(self.root)
        self.label_source9.place(x=100,y=550,width=121,height=30)
        self.sourceEntry9=tk.Entry(self.root)
        self.sourceEntry9.place(x=220,y=550,width=200,height=30)
        self.chk_WS9=tk.Checkbutton(self.root)
        self.chk_WS9.place(x=425,y=550,width=70,height=30)

        self.label_source10=tk.Label(self.root)
        self.label_source10.place(x=100,y=585,width=121,height=30)
        self.sourceEntry10=tk.Entry(self.root)
        self.sourceEntry10.place(x=220,y=585,width=200,height=30)
        self.chk_WS10=tk.Checkbutton(self.root)
        self.chk_WS10.place(x=425,y=585,width=70,height=30)

        self.label_source11=tk.Label(self.root)
        #self.label_source11.place(x=100,y=625,width=121,height=30)
        self.sourceEntry11=tk.Entry(self.root)
        #self.sourceEntry11.place(x=220,y=625,width=200,height=30)
        self.chk_WS11=tk.Checkbutton(self.root)
        #self.chk_WS11.place(x=425,y=625,width=70,height=30)

        self.label_source12=tk.Label(self.root)
        #self.label_source12.place(x=100,y=660,width=121,height=30)
        self.sourceEntry12=tk.Entry(self.root)
        #self.sourceEntry12.place(x=220,y=660,width=200,height=30)
        self.chk_WS12=tk.Checkbutton(self.root)
        #self.chk_WS12.place(x=425,y=660,width=70,height=30)


    def populateWindow(self):
        #Window
        self.root.title("Workstation Data Recorder - Version " + self.config.get('version_info','versionNumber'))
        width=650
        height=780
        width *= self.expandWidth
        # height *= self.expandHeight

        screenwidth = self.root.winfo_screenwidth()
        screenheight = self.root.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.root.geometry(alignstr)
        self.root.resizable(width=False, height=False)
        self.root.config(bg= "#383838")

        self.label_SwTitle=tk.Label(self.root)
        self.label_SwTitle["anchor"] = "center"
        self.label_SwTitle["bg"] = "#383838"
        ft = tkFont.Font(family='Verdana',size=24)
        self.label_SwTitle["font"] = ft
        self.label_SwTitle["fg"] = "#79a878"#"#69a078"
        self.label_SwTitle["justify"] = "center"
        self.label_SwTitle["text"] = "WORKSTATION DATA RECORDER"
        self.label_SwTitle.place(x=195,y=20,width=560,height=75)

        #Status frame
        self.statusFrame = tk.Frame(self.root)
        self.statusFrame["background"] = "dark gray"
        self.statusFrame.place(x=580,y=120,height=135,width=250)
        self.label_stats = tk.Label(self.statusFrame)
        self.label_stats["background"] = "dark gray"
        self.label_stats.place(x=5,y=5)
        self.label_stats["text"]= "                    DCP STATUS                     "
        self.label_stats["justify"]= "center"
        self.label_stats["fg"]= "dark blue"

        self.label_HDD_Message_A = tk.Label(self.statusFrame)
        self.label_HDD_Message_A["background"] = "dark gray"
        self.label_HDD_Message_A.place(x=5,y=60)
        self.label_HDD_Message_A["fg"] = "dark red"

        self.label_HDD_Message_B = tk.Label(self.statusFrame)
        self.label_HDD_Message_B["background"] = "dark gray"
        self.label_HDD_Message_B.place(x=5,y=110)
        self.label_HDD_Message_B["fg"] = "dark red"

        self.label_HDD_Status = tk.Label(self.statusFrame)
        self.label_HDD_Status["background"] = "dark gray"
        self.label_HDD_Status.place(x=5,y=35)
        self.label_HDD_Status["fg"] = "black"
        hdd_1 = shutil.disk_usage('/mnt/dd1')
        self.label_HDD_Status["text"]= f"Disk A -Free Space: "#{(hdd.free / 2**30):.2f} GB"
        self.label_HDD_Space = tk.Label(self.statusFrame)
        self.label_HDD_Space["background"] = "dark gray"
        self.label_HDD_Space["fg"] = "black"
        self.label_HDD_Space.place(x=135,y=35)
        self.label_HDD_Space["text"]= f"  {(hdd_1.free / 2**30):.2f} GB"

        if ((hdd_1.free / 2**30)) < 350.00:
            self.label_HDD_Space["fg"] = "red"
            self.label_HDD_Message_A['text']= "         Data Will Be Overwritten"
        elif ((hdd_1.free / 2**30)) < 450.00:
            self.label_HDD_Space["fg"] = "e0d900"

        self.label_HDD_Status_2 = tk.Label(self.statusFrame)
        self.label_HDD_Status_2["background"] = "dark gray"
        self.label_HDD_Status_2.place(x=5,y=85)
        self.label_HDD_Status_2["fg"] = "black"
        hdd_2 = shutil.disk_usage('/mnt/dd2')
        self.label_HDD_Status_2["text"]= f"Disk B -Free Space: "#{(hdd.free / 2**30):.2f} GB"
        self.label_HDD_Space_2 = tk.Label(self.statusFrame)
        self.label_HDD_Space_2["background"] = "dark gray"
        self.label_HDD_Space_2["fg"] = "black"
        self.label_HDD_Space_2.place(x=135,y=85)
        self.label_HDD_Space_2["text"]= f"  {(hdd_2.free / 2**30):.2f} GB"

        if ((hdd_2.free / 2**30)) < 350.00:
            self.label_HDD_Space_2["fg"] = "red"
            self.label_HDD_Message_B['text']= "         Data Will Be Overwritten"
        elif ((hdd_2.free / 2**30)) < 450.00:
            self.label_HDD_Space_2["fg"] = "e0d900"

        #Menu bar
        menubar = Menu(self.root, background='#ff8000', foreground='black', activebackground='gray', activeforeground='black')
        file = Menu(menubar, tearoff=0)
        #file.add_command(label="New Recording", command= self.menuNewRecording)
        if(g.config.get('dev_tools','includePlayback') == '1'):
            file.add_command(label="Open Playback", command= lambda: self.openPlayback(playbackGUI))
        file.add_separator()
        file.add_command(label="Exit", command= self.root.quit)
        menubar.add_cascade(label="File", menu=file)

        help = Menu(menubar, tearoff=0)
        help.add_command(label="Instructions", command= self.openInstructions)
        menubar.add_cascade(label="Help", menu=help)
        self.root.config(menu=menubar)
        #Filepath/Directory
        self.label_SaveDest=tk.Label(self.root)
        self.label_SaveDest["activebackground"] = "#383838"
        self.label_SaveDest["anchor"] = "w"
        self.label_SaveDest["bg"] = "#383838"
        ft = tkFont.Font(family='Verdana',size=10)
        self.label_SaveDest["font"] = ft
        self.label_SaveDest["fg"] = "light gray"
        self.label_SaveDest["justify"] = "center"
        self.label_SaveDest["text"] = "Save Directory: "
        self.label_SaveDest.place(x=100,y=120,width=121,height=30)

        self.entry_SaveDir=tk.Entry(self.root)
        self.entry_SaveDir["borderwidth"] = "1px"
        ft = tkFont.Font(family='Verdana',size=10)
        self.entry_SaveDir["font"] = ft
        self.entry_SaveDir["fg"] = "#333333"
        self.entry_SaveDir["justify"] = "center"
        self.entry_SaveDir["text"] = ""
        self.entry_SaveDir.place(x=220,y=120,width=280,height=30)


        self.entry_SaveDir.insert(0,g.paths['viddir'])
        self.entry_SaveDir.xview_moveto(1)
        self.entry_SaveDir.config(state= DISABLED)

        self.parentDirectory = g.paths['viddir']

        #Stopwatch
        self.stopWatch = Stopwatch.StopWatch(self.root)
        self.stopWatch.place(x=235,y=165, width=75,height=30)

        #Buttons
        self.button_BrowseDestination=tk.Button(self.root)
        self.button_BrowseDestination["bg"] = "#efefef"
        ft = tkFont.Font(family='Verdana',size=10)
        self.button_BrowseDestination["font"] = ft
        self.button_BrowseDestination["fg"] = "#000000"
        self.button_BrowseDestination["justify"] = "center"
        self.button_BrowseDestination["text"] = "Browse"
        self.button_BrowseDestination["command"] = self.chooseDirectory
        if (self.config.get('dev_tools','devEditableSaveLocation')) == '1':
            self.button_BrowseDestination["state"] = NORMAL
            self.button_BrowseDestination.place(x=20,y=120,width=75,height=30)
        else:
            self.button_BrowseDestination["state"] = DISABLED


        self.button_Record=tk.Button(self.root)
        self.button_Record["bg"] = "#efefef"
        ft = tkFont.Font(family='Verdana',size=10)
        self.button_Record["font"] = ft
        self.button_Record["fg"] = "#000000"
        self.button_Record["justify"] = "center"
        self.button_Record["text"] = "Record"
        self.button_Record.place(x=315,y=165,width=145,height=30)
        self.button_Record["command"] = self.toggleRecord


        self.bool_checkedAllWorkstations = BooleanVar()
        self.WS_All=tk.Checkbutton(self.root)
        ft = tkFont.Font(family='Verdana',size=10)
        self.WS_All["font"] = ft
        self.WS_All["fg"] = "light gray"
        self.WS_All["background"] = "#383838"
        self.WS_All["justify"] = "center"
        self.WS_All["text"] = "ALL"
        self.WS_All["offvalue"] = False
        self.WS_All["onvalue"] = True
        self.WS_All["variable"] = self.bool_checkedAllWorkstations
        self.WS_All["command"] = self.checkAllWorkstations
        self.WS_All.place(x=425,y=240,width=70,height=25)

        self.chk_Duration = tk.Checkbutton()
        ft = tkFont.Font(family='Verdana',size=10)
        self.chk_Duration["font"] = ft
        self.chk_Duration["justify"] = "center"
        self.chk_Duration["text"] = "  DURATION (m)"
        self.chk_Duration["offvalue"] = False
        self.chk_Duration["onvalue"] = True
        self.chk_Duration["variable"] = self.bool_useDuration
        self.chk_Duration["command"] = self.toggleEntry_Duration
        self.chk_Duration.place(x=235,y=205,width=150,height=25)

        self.entry_duration = tk.Entry(self.root)
        self.entry_duration["borderwidth"] = "1px"
        ft = tkFont.Font(family='Verdana',size=10)
        self.entry_duration["font"] = ft
        self.entry_duration["fg"] = "#333333"
        self.entry_duration["justify"] = "center"
        self.entry_duration["textvariable"] = self.duration
        self.entry_duration.place(x=390,y=205,width=70,height=25)

        for src in self.sourceInputList:
            idx = self.sourceInputList.index(src)
            cfgText = f"WS{idx+1}"
            src.set(self.config.get('dcp_config',cfgText))
        for lbl in self.sourceLabelList:
            idx = self.sourceLabelList.index(lbl)
            if idx < 10:
                txt = f"Workstation {idx+1:02}: "
            else:
                txt = f"Shelter {idx - 9:02}: "
            lbl["text"] = txt
            lbl["activebackground"] = "#383838"
            lbl["anchor"] = "w"
            lbl["bg"] = "#383838"
            ft = tkFont.Font(family='Verdana',size=10)
            lbl["font"] = ft
            lbl["fg"] = "light gray"
            lbl["justify"] = "center"
        for ent in self.sourceEntryList:
            idx = self.sourceEntryList.index(ent)
            ent["borderwidth"] = "1px"
            ft = tkFont.Font(family='Verdana',size=10)
            ent["font"] = ft
            ent["fg"] = "#333333"
            ent["justify"] = "center"
            ent["textvariable"] = self.sourceInputList[idx]
            ent["state"] = DISABLED
        for chk in self.chkBoxList:
            idx = self.chkBoxList.index(chk)
            if idx < 10:
                txt = f"WS{idx+1:02}"
            else:
                txt = f"Sh{idx - 9:02}"
            ft = tkFont.Font(family='Verdana',size=10)
            chk["text"] = txt
            chk["font"] = ft
            chk["fg"] = "#333333"
            chk["justify"] = "center"
            chk["offvalue"] = False
            chk["onvalue"] = True
            chk["variable"] = self.workstationBoolList[idx]

        self.createStatusLabels()
        #self.useDevSize(self.sizeFlag)

    def useDevSize(self,val):
        if val == '1':
            self.label_SwTitle.place(x=195,y=20,width=560,height=75)
            self.label_SaveDest.place(x=100,y=120,width=121,height=30)
            self.entry_SaveDir.place(x=220,y=120,width=280,height=30)
            self.stopWatch.place(x=235,y=165, width=75,height=30)
            self.button_Record.place(x=315,y=165,width=145,height=30)
            self.chk_Duration.place(x=235,y=205,width=150,height=25)
            self.entry_duration.place(x=390,y=205,width=70,height=25)
            self.WS_All.place(x=425,y=240,width=70,height=25)
            self.label_source1.place(x=100,y=270,width=121,height=30)
            self.sourceEntry1.place(x=220,y=270,width=200,height=30)
            self.chk_WS1.place(x=425,y=270,width=70,height=30)
            self.label_source2.place(x=100,y=305,width=121,height=30)
            self.sourceEntry2.place(x=220,y=305,width=200,height=30)
            self.chk_WS2.place(x=425,y=305,width=70,height=30)
            self.label_source3.place(x=100,y=340,width=121,height=30)
            self.sourceEntry3.place(x=220,y=340,width=200,height=30)
            self.chk_WS3.place(x=425,y=340,width=70,height=30)
            self.label_source4.place(x=100,y=375,width=121,height=30)
            self.sourceEntry4.place(x=220,y=375,width=200,height=30)
            self.chk_WS4.place(x=425,y=375,width=70,height=30)
            self.label_source5.place(x=100,y=410,width=121,height=30)
            self.sourceEntry5.place(x=220,y=410,width=200,height=30)
            self.chk_WS5.place(x=425,y=410,width=70,height=30)
            self.label_source6.place(x=100,y=445,width=121,height=30)
            self.sourceEntry6.place(x=220,y=445,width=200,height=30)
            self.chk_WS6.place(x=425,y=445,width=70,height=30)
            self.label_source7.place(x=100,y=480,width=121,height=30)
            self.sourceEntry7.place(x=220,y=480,width=200,height=30)
            self.chk_WS7.place(x=425,y=480,width=70,height=30)
            self.label_source8.place(x=100,y=515,width=121,height=30)
            self.sourceEntry8.place(x=220,y=515,width=200,height=30)
            self.chk_WS8.place(x=425,y=515,width=70,height=30)
            self.label_source9.place(x=100,y=550,width=121,height=30)
            self.sourceEntry9.place(x=220,y=550,width=200,height=30)
            self.chk_WS9.place(x=425,y=550,width=70,height=30)
            self.label_source10.place(x=100,y=585,width=121,height=30)
            self.sourceEntry10.place(x=220,y=585,width=200,height=30)
            self.chk_WS10.place(x=425,y=585,width=70,height=30)
            self.label_source11.place(x=100,y=625,width=121,height=30)
            self.sourceEntry11.place(x=220,y=625,width=200,height=30)
            self.chk_WS11.place(x=425,y=625,width=70,height=30)
            self.label_source12.place(x=100,y=660,width=121,height=30)
            self.sourceEntry12.place(x=220,y=660,width=200,height=30)
            self.chk_WS12.place(x=425,y=660,width=70,height=30)
        else:
            pass

# Main
if __name__ == "__main__":
    root = tk.Tk()
    app = WorkstationDataRecorder_GUI(root)
    root.mainloop()
