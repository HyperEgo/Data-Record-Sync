import tkinter as tk
import tkinter.font as tkFont
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
import os
import sys
import configparser
import datetime
import shutil
import threading
import time

from global_vars import g
from utils import utils
from VidRecorder import VidRecorder
from PlaybackWindow_GUI import PlaybackWindow_GUI as playbackGUI
import utils.vidlogging as vidlogging
import libs.modifiedTKV as tkVid
import libs.ToolTips as tooltip
import libs.Stopwatch as Stopwatch
from DriveManager import DriveManager

sys.path.append("../log_project")
import fake_log_generator
import log_parser

# Set up logger
logger = vidlogging.get_logger('RECORD_GUI',filename=g.paths['logfile'])

class GuiError(Exception):
    """A custom exception used to report errors in pulling out values from the gui"""
    def __init___( self, message, error_type, error_info ):
        super().__init__(message)

class WorkstationDataRecorder_GUI:
    def __init__(self, root, config):

        self.root = root
        self.config = config

        curdir = os.getcwd()
        self.parentDirectory = StringVar()
        self.recorder = None
        self.ip_info = {} # dict, matches each ip address to its wid, valid_ping, and valid_format

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

        self.img_red = PhotoImage(file = "assets/icons/redLight.gif")
        self.img_green = PhotoImage(file = "assets/icons/greenLight.gif")
        self.img_dark = PhotoImage(file = "assets/icons/noLight.gif")

        self.initSources()
        self.makeLists()
        self.populateWindow()
        self.toggleEntry_Duration()



        # Validate all ip addresses before doing anything
        if g.advanced['ping_rna_onlaunch']:
            # pinging twice at startup to allow for detection after a reboot
            # otherwise it shows the rna's as not connected when they really are
            self.ping_rnas(
                ping_timeout_sec=g.advanced['ping_rna_timeout_sec'],
                ping_count=g.advanced['ping_rna_onlaunch_count'],
            )

#Functions

    def ping_rnas(self, ping_timeout_sec=1, ping_count=1):
        # Validate all ip addresses before doing anything
        self.clearAllStatusLabels()
        ping_info = {
            'run_ping_test': True,
            'timeout_sec': ping_timeout_sec,
            'count': ping_count,
        }
        check_ip_timer = threading.Timer(1.0, self.validate_ip_address_list, [ping_info])
        check_ip_timer.daemon = True
        check_ip_timer.start()

    def createStatusLabels(self):
        xPos = 525
        yPos = 330
        for lbl in self.statusLabelList:
            lbl["justify"] = "center"
            lbl["fg"] = "light gray"
            lbl["background"] = "#383838"
            lbl["font"] = tkFont.Font(family='Verdana',size=-14)
            lbl.place(x=xPos,y=yPos)#,width=70,height=30)
            yPos += 35

    def updateStatusLabels(self,workstation_info,record_state=None):
        print(f'Inside updateStatusLabels -- record state: {record_state}')
        # workstation_info is list of dicts from VidRecorder.get_workstation_info
        # workstation_info[i]['update_stats'] is corresponding dict from DriveManager.calc_chapter_stats
        for w in workstation_info:
            # print(w)
            wid = w['wsid_int']
            update_stats = w['last_update_stats']
            # no_processes = not any(w["process_info"])
            no_processes = (not w["process_info"]["main"] and
                            not w["process_info"]["overlap"])

            short_desc = w["short_desc"]
            current_state = w["current_state"]
            chapter_count = w["chapter_count"]
            chapter_size_main = w["chapter_size_main"]
            total_vid_size = w["total_vid_size"]
            # update_stats_all_None = all([info == None for info in update_stats['process_info']])

            print(short_desc)
            # process = w['process_info']['main']
            # line += '   main    : '
            # if process:
            #     line = f'{process.one_line_desc()}\n'
            # process = w['process_info']['overlap']
            # line += '   overlap : '
            # if process:
            #     line += f'{process.one_line_desc()}\n'
            # print(line)

            lbl_idx = wid-1
            if lbl_idx >= 0 and lbl_idx < len(self.statusLabelList):
                lbl = self.statusLabelList[lbl_idx]
                if record_state == 'started' and no_processes:
                    text = "Pending..."
                # elif record_state == 'sdp_download' and update_stats_all_None and w['sdp_downloaded'] == False:
                elif record_state == 'sdp_download' and no_processes and w['sdp_downloaded'] == False:
                    text = f'Workstation SDP download failed.'
                # elif record_state == 'sdp_download' and update_stats_all_None and w['sdp_downloaded'] == True:
                elif record_state == 'sdp_download' and no_processes and w['sdp_downloaded'] == True:
                    text = f'Workstation SDP download success.'
                elif record_state == 'started' and not w['is_recording']: # w['filestats']['size']
                    text = f"Establishing connection. Please wait..."
                elif record_state == 'started' and w['is_recording']:
                    # if ws_stats and ws_stats['filestats'] != None:
                    text = f"Recording... | " \
                        f"{utils.bytesto_string(chapter_size_main)} / {utils.bytesto_string(total_vid_size)} ({w['chapter_count']})"
                        # self.stopWatch.Start()
                elif record_state == 'stopped':
                    # if ws_stats:
                    text = f"Stopped | File size: {utils.bytesto_string(total_vid_size)}"
                    # self.stopWatch.Stop()
                else:
                    text = f'({record_state}|{no_processes}|{w["sdp_downloaded"]})'
                    print(w["process_info"])
                    # text = f'ERROR: Unknown recording state in gui'

                print(text)
                lbl.configure(text = text)

    def openPlayback(self, _class):#TODO: Obsolete. Should be broken off into a separate app.
        if(self.playWin_toplevel is None):
            self.root.iconify()
            self.playWin_toplevel = tk.Toplevel(self.root)
            self.playWin_toplevel.protocol('WM_DELETE_WINDOW',self.onPlaybackClose)
            _class(self.playWin_toplevel,self.config)
            print('End openPlayback')

    def onPlaybackClose(self):#TODO: Obsolete once playback is broken off into a separate app.
        self.playWin_toplevel.destroy()
        self.playWin_toplevel = None

    def openTkVid(self):
        self.root.iconify()
        tkVid(self.new)

    def clearAllStatusLabels(self):
        for lbl in self.statusLabelList:
            lbl.configure(text=' ')

    def toggleRecord(self): # callback for Record/Stop button
        if(not self.recorder or self.recorder.is_recording == False):
            self.startRecordAll()
        else:
            self.stopRecordAll()

    def validate_ip_address_list(self, ping_info, update_labels=True):
        ips = {}
        run_ping_test    = ping_info['run_ping_test']
        ping_timeout_sec = ping_info['timeout_sec']
        ping_count       = ping_info['count']

        for idx,src in enumerate(self.ipAddresses):
            ip = src.get()

            (valid_format,valid_ping) = utils.validate_ip(
                ip, run_ping_test=run_ping_test, ping_timeout_sec=ping_timeout_sec, ping_count=ping_count)
            ping_result = "success" if valid_ping else "failed"
            logger.info(f'Ping test: {ip} ... {ping_result}')

            ips[ip] = {'wid': idx+1, 'valid_format': valid_format, 'valid_ping': valid_ping}
            if update_labels:
                self.update_ip_status_labels(ips[ip],run_ping_test)

        self.ip_info = ips
        return ips

    def update_ip_status_labels(self,ip_info,ping_test=False):
        text = None
        lightStatus = 0
        if not ip_info['valid_format']:
            text = 'Invalid IP formatting. Check dcp_config.txt'
        elif ping_test:
            if not ip_info['valid_ping']:
                text = 'Not connected. Ping test failed.'
                lightStatus = 1
            else:
                text = 'Connected.'
                lightStatus = 2
        if text:
            lbl_idx = ip_info['wid']-1
            if lbl_idx >= 0 and lbl_idx < len(self.statusLabelList):
                lbl = self.statusLabelList[lbl_idx]
                lbl.configure(text = text)
                self.update_ping_light(self.pingLightList[lbl_idx],self.pingLightTTPList[lbl_idx],lightStatus)

    def update_ping_light(self,imageObj,tooltipObj,status):
        '''
        Updates the red/green/dark icon displayed next to the workstation status labels. The color and tooltip text will change according to the workstation IP status.
        '''
        if status == 2:
            imageObj["image"] = self.img_green
            tooltipObj = tooltip.CreateToolTip(imageObj, "Connected")
        elif status == 1:
            imageObj["image"] = self.img_red
            tooltipObj = tooltip.CreateToolTip(imageObj, "Not Connected")
        else:
            imageObj["image"] = self.img_dark
            tooltipObj = tooltip.CreateToolTip(imageObj, "Invalid")

    def get_selected_workstations(self): #TODO: Will be obsolete. Need to just record all connected devices when Vidrecorder starts.
        workstations = []

        for idx,src in enumerate(self.ipAddresses):
            ip = src.get()
            workstation_selected = self.workstationBoolList[idx].get() == True
            workstation_valid_ping = self.ip_info[ip]['valid_ping'] == True if ip in self.ip_info.keys() else False
            if workstation_selected:
                workstations.append(
                    {
                        "id": int(ip[-2:]) % 70 if len(ip) > 2 else -1,
                        "ip": ip,
                        "valid_ping": workstation_valid_ping,
                        # "dir": wsDirectory
                    }
                )

        return workstations


    def startRecordAll(self, valid_pings_only=True): #TODO: Will be obsolete once functionality is moved. Update will probably be sent to GUI elsewhere.

        logger.debug(f'startRecordAll')

        # # Get and validate duration from gui
        self.duration = 0 # TODO: Obsolete .. remove all references to this when able

        # Make sure user has selected workstations to be recorded before proceeding
        # Get list of selected workstations
        workstations = self.get_selected_workstations() #TODO: Obsolete when autostart is implemented. All connected WS's will be recorded.
        if len(workstations) <= 0:
            messagebox.showinfo('Input Error', 'No workstations selected', parent=self.root)
            return

        # Make sure the ips have been pinged before proceeding
        any_valid_pings = True
        # TODO: put this back in after developing
        # any_valid_pings = False
        # for ws in workstations:
        #     if ws['valid_ping']:
        #         any_valid_pings = True
        #         break
        # if not any_valid_pings:
        #     messagebox.showinfo('Input Error', 'No valid pings. Run File->Ping RNAs', parent=self.root)
        #     return

        logger.debug(f'selected workstations: {workstations}')

        # Mark start of record time
        self.begin = time.localtime()

        # Create the almighty VidRecorder object -- this guys manages all of the DeviceRecorders
        if (self.recorder is None):
            use_dev_dir  = g.dev_opts['devDirectory']
            self.recorder = VidRecorder(workstations, hdd=g.paths['hdd'], duration=self.duration,
                update_callback=self.on_vidrecorder_update, use_dev_dir=use_dev_dir)

        # Clear all of the status labels before trying to start the recorders
        self.clearAllStatusLabels()

        try:
            if not self.recorder.is_recording:
                self.recorder.start()

                # if recorder successfully starts
                if self.recorder and self.recorder.is_recording:
                    # Put GUI in 'record start' state
                    self.bool_IsRecording = True
                    self.button_Record["text"] = "Stop"
                    # Disable any gui controls that shouldn't be available during recording operation
                    for chk in self.chkBoxList:
                        chk["state"]= DISABLED

        except:
            print("Unable to begin recording. Start Recording command failed.")
            messagebox.showinfo('Start Command Failure', "Unable to begin recording.", parent=self.root)

            # Put GUI in 'record stop' state
            self.bool_IsRecording = False
            self.button_Record["text"] = "Record"
            for chk in self.chkBoxList:
                chk['state'] = NORMAL
            self.stopWatch.Reset() #TODO: Move to Vidrecorder.


    def get_float_from_entrybox(self,box,label):
        #TODO: Obsolete once autostart is implemented. Recording duration will presumably be continuous until manually stopped.
        value = None
        valid = False
        try:
            value = float(box.get())
            valid = True
        except ValueError as e:
            messagebox.showinfo('Input Error', f'Invalid {label} Value', parent=self.root)
            box.delete(0,'end')
        return value,valid

    def stopRecordAll(self):

        logger.debug(f'stopRecordAll')
        logger.debug(self.recorder)
        logger.debug(f'is_recording: {self.recorder.is_recording}' if self.recorder else "recorder is None")

        # Stop the vidrecorder
        if (self.recorder and self.recorder.is_recording):
            logger.debug(f'self.recorder.is_recording is True -- calling self.recorder.stop()')
            self.recorder.stop()

        #Delete session directory if nothing was recorded.
        # if(os.listdir(self.recorder.sessionDirectory) == []):#TODO: Is a directory created still if nothing is recorded?
        #     os.rmdir(self.recorder.sessionDirectory)

        if self.recorder:
            self.end = time.localtime()
            # if((self.config.get('dev_tools','devLogCreator')) == '1'):
            if ( g.dev_opts['devLogCreator'] ):
                fake_log_generator.generate_log(self.begin, self.end, dir_path=self.recorder.sessionDirectory + "/logs/")
            # self.stopWatch.Stop()
            self.bool_IsRecording = False
            self.button_Record["text"] = "Record"

        self.recorder = None

    # def OnStopRecordingHandler(self,info=None):
    #     # update gui with info if needed #TODO: Is this function still needed?
    #     pass

    def on_vidrecorder_update(self,update):
        print(f'===================gui on_vidrecorder_update -- {update["type"]}')
        if (update['type'] == 'Update'):
            workstation_info = update['workstation_info']

            #update save directory entry box
            if g.paths['viddir'] is not self.entry_SaveDir.get():
                self.entry_SaveDir.config(state= NORMAL)
                self.entry_SaveDir.delete(0,'end')
                self.entry_SaveDir.insert(0,g.paths['viddir'])
                self.entry_SaveDir.config(state= DISABLED)

            self.updateStatusLabels(workstation_info,record_state='started')

            video_storage = update['video_storage'] # list of dicts

            # Show "Active" label on drive that is currently being recorded
            if(video_storage[0]['active']):
                self.label_Active_HDD.place(x = 300,y=35)
                self.Active_Image.place(x=5,y=35) #TODO: Need to create a new image for the event frame. Background color issue. This should work otherwise.
                self.Inactive_Image.place(x=5,y=120)
            elif(video_storage[1]['active']):
                self.label_Active_HDD.place(x = 300,y=120)
                self.Active_Image.place(x=5,y=120)
                self.Inactive_Image.place(x=5,y=35)

            for i,drive_info in enumerate(video_storage):
                if drive_info['actual_pct_used_breach']: # bad bad bad over the limit
                    self.diskLabelList_Space[i]["fg"] = "dark red"
                    self.diskLabelList_Warning[i]['text']= "Disk At Capacity Limit."
                elif drive_info['actual_pct_used_warning']: # warning
                    self.diskLabelList_Space[i]["fg"] = "#e0d900"
                    self.diskLabelList_Warning[i]['text']= ""
                else:
                    self.diskLabelList_Space[i]["fg"] = "black"
                    self.diskLabelList_Warning[i]['text']= ""

                # drive_info['stats']
                # usage(total=7620804153344, used=11235618816, free=7225476755456)
                freespace = utils.bytesto(drive_info['stats'].free,'gb')
                storage_text = f"{freespace:.2f} GB"
                self.diskLabelList_Space[i]["text"] = storage_text

                capacity_text = f'  {drive_info["actual_pct_used"]*100:.2f}% Used of {utils.bytesto(drive_info["actual_capacity"],"gb"):.2f} GB Available Space'
                self.diskLabelList_Percent[i]["text"] = capacity_text

        elif(update['type'] == 'Recording started'):
            logger.info('---------------------------------')
            logger.info('RECORDING STARTED -- update to gui here')
            logger.info('---------------------------------')

            # Update stop watch
            self.stopWatch.Reset()

        elif(update['type'] == 'Recording stopped'):
            logger.info('---------------------------------')
            logger.info('RECORDING STOPPED -- update to gui here')
            logger.info('---------------------------------')
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

    def checkAllWorkstations(self):
        #TODO: Soon to be obsolete. Recording will occur for all available/connected workstations.
        flag = False
        for chk in self.workstationBoolList:
            idx = self.workstationBoolList.index(chk)
            chk.set(self.bool_checkedAllWorkstations.get())

    def toggleEntry_Duration(self):
        #TODO: Soon to be obsolete. User will not need duration settings, since duration will presumably be continuous until manually stopped.
        if(self.entry_duration["state"] == NORMAL):
            self.entry_duration.config(state=DISABLED)
        else:
            self.entry_duration.config(state=NORMAL)

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
                                self.label_source10]
                                # self.label_source11,
                                # self.label_source12]

        self.ipAddresses = [self.source1,
                                self.source2,
                                self.source3,
                                self.source4,
                                self.source5,
                                self.source6,
                                self.source7,
                                self.source8,
                                self.source9,
                                self.source10]
                                # self.source11,
                                # self.source12]

        self.sourceEntryList = [self.sourceEntry1,
                                self.sourceEntry2,
                                self.sourceEntry3,
                                self.sourceEntry4,
                                self.sourceEntry5,
                                self.sourceEntry6,
                                self.sourceEntry7,
                                self.sourceEntry8,
                                self.sourceEntry9,
                                self.sourceEntry10]
                                # self.sourceEntry11,
                                # self.sourceEntry12]

        self.workstationBoolList = [self.bool_WS1,
                                    self.bool_WS2,
                                    self.bool_WS3,
                                    self.bool_WS4,
                                    self.bool_WS5,
                                    self.bool_WS6,
                                    self.bool_WS7,
                                    self.bool_WS8,
                                    self.bool_WS9,
                                    self.bool_WS10]
                                    # self.bool_WS11,
                                    # self.bool_WS12]

        self.chkBoxList = [self.chk_WS1,
                           self.chk_WS2,
                           self.chk_WS3,
                           self.chk_WS4,
                           self.chk_WS5,
                           self.chk_WS6,
                           self.chk_WS7,
                           self.chk_WS8,
                           self.chk_WS9,
                           self.chk_WS10]
                        #    self.chk_WS11,
                        #    self.chk_WS12]

        self.statusLabelList = [self.label_ws1_recordingStatus,
                                self.label_ws2_recordingStatus,
                                self.label_ws3_recordingStatus,
                                self.label_ws4_recordingStatus,
                                self.label_ws5_recordingStatus,
                                self.label_ws6_recordingStatus,
                                self.label_ws7_recordingStatus,
                                self.label_ws8_recordingStatus,
                                self.label_ws9_recordingStatus,
                                self.label_ws10_recordingStatus]
                                # self.label_ws11_recordingStatus,
                                # self.label_ws12_recordingStatus]

        self.pingLightList = [self.img_WS1,
                              self.img_WS2,
                              self.img_WS3,
                              self.img_WS4,
                              self.img_WS5,
                              self.img_WS6,
                              self.img_WS7,
                              self.img_WS8,
                              self.img_WS9,
                              self.img_WS10]

        self.pingLightTTPList = [self.img_WS1_ttp,
                                self.img_WS2_ttp,
                                self.img_WS3_ttp,
                                self.img_WS4_ttp,
                                self.img_WS5_ttp,
                                self.img_WS6_ttp,
                                self.img_WS7_ttp,
                                self.img_WS8_ttp,
                                self.img_WS9_ttp,
                                self.img_WS10_ttp]



    def initSources(self):
        self.label_source1=tk.Label(self.root)
        self.label_source1.place(x=100,y=325,width=121,height=30)
        self.sourceEntry1=tk.Entry(self.root)
        self.sourceEntry1.place(x=220,y=325,width=200,height=30)
        self.chk_WS1=tk.Checkbutton(self.root)
        self.chk_WS1.place(x=425,y=325,width=70,height=30)
        self.img_WS1 = Label(self.root,image=self.img_dark,borderwidth=0)
        self.img_WS1.place(x=500,y=330)
        self.img_WS1_ttp = tooltip.CreateToolTip(self.img_WS1, '')

        self.label_source2=tk.Label(self.root)
        self.label_source2.place(x=100,y=360,width=121,height=30)
        self.sourceEntry2=tk.Entry(self.root)
        self.sourceEntry2.place(x=220,y=360,width=200,height=30)
        self.chk_WS2=tk.Checkbutton(self.root)
        self.chk_WS2.place(x=425,y=360,width=70,height=30)
        self.img_WS2 = Label(self.root,image=self.img_dark,borderwidth=0)
        self.img_WS2.place(x=500,y=365)
        self.img_WS2_ttp = tooltip.CreateToolTip(self.img_WS2, '')

        self.label_source3=tk.Label(self.root)
        self.label_source3.place(x=100,y=395,width=121,height=30)
        self.sourceEntry3=tk.Entry(self.root)
        self.sourceEntry3.place(x=220,y=395,width=200,height=30)
        self.chk_WS3=tk.Checkbutton(self.root)
        self.chk_WS3.place(x=425,y=395,width=70,height=30)
        self.img_WS3 = Label(self.root,image=self.img_dark,borderwidth=0)
        self.img_WS3.place(x=500,y=400)
        self.img_WS3_ttp = tooltip.CreateToolTip(self.img_WS3, '')

        self.label_source4=tk.Label(self.root)
        self.label_source4.place(x=100,y=430,width=121,height=30)
        self.sourceEntry4=tk.Entry(self.root)
        self.sourceEntry4.place(x=220,y=430,width=200,height=30)
        self.chk_WS4=tk.Checkbutton(self.root)
        self.chk_WS4.place(x=425,y=430,width=70,height=30)
        self.img_WS4 = Label(self.root,image=self.img_dark,borderwidth=0)
        self.img_WS4.place(x=500,y=435)
        self.img_WS4_ttp = tooltip.CreateToolTip(self.img_WS4, '')

        self.label_source5=tk.Label(self.root)
        self.label_source5.place(x=100,y=465,width=121,height=30)
        self.sourceEntry5=tk.Entry(self.root)
        self.sourceEntry5.place(x=220,y=465,width=200,height=30)
        self.chk_WS5=tk.Checkbutton(self.root)
        self.chk_WS5.place(x=425,y=465,width=70,height=30)
        self.img_WS5 = Label(self.root,image=self.img_dark,borderwidth=0)
        self.img_WS5.place(x=500,y=470)
        self.img_WS5_ttp = tooltip.CreateToolTip(self.img_WS5, '')

        self.label_source6=tk.Label(self.root)
        self.label_source6.place(x=100,y=500,width=121,height=30)
        self.sourceEntry6=tk.Entry(self.root)
        self.sourceEntry6.place(x=220,y=500,width=200,height=30)
        self.chk_WS6=tk.Checkbutton(self.root)
        self.chk_WS6.place(x=425,y=500,width=70,height=30)
        self.img_WS6 = Label(self.root,image=self.img_dark,borderwidth=0)
        self.img_WS6.place(x=500,y=505)
        self.img_WS6_ttp = tooltip.CreateToolTip(self.img_WS6, '')

        self.label_source7=tk.Label(self.root)
        self.label_source7.place(x=100,y=535,width=121,height=30)
        self.sourceEntry7=tk.Entry(self.root)
        self.sourceEntry7.place(x=220,y=535,width=200,height=30)
        self.chk_WS7=tk.Checkbutton(self.root)
        self.chk_WS7.place(x=425,y=535,width=70,height=30)
        self.img_WS7 = Label(self.root,image=self.img_dark,borderwidth=0)
        self.img_WS7.place(x=500,y=540)
        self.img_WS7_ttp = tooltip.CreateToolTip(self.img_WS7, '')

        self.label_source8=tk.Label(self.root)
        self.label_source8.place(x=100,y=570,width=121,height=30)
        self.sourceEntry8=tk.Entry(self.root)
        self.sourceEntry8.place(x=220,y=570,width=200,height=30)
        self.chk_WS8=tk.Checkbutton(self.root)
        self.chk_WS8.place(x=425,y=570,width=70,height=30)
        self.img_WS8 = Label(self.root,image=self.img_dark,borderwidth=0)
        self.img_WS8.place(x=500,y=575)
        self.img_WS8_ttp = tooltip.CreateToolTip(self.img_WS8, '')

        self.label_source9=tk.Label(self.root)
        self.label_source9.place(x=100,y=605,width=121,height=30)
        self.sourceEntry9=tk.Entry(self.root)
        self.sourceEntry9.place(x=220,y=605,width=200,height=30)
        self.chk_WS9=tk.Checkbutton(self.root)
        self.chk_WS9.place(x=425,y=605,width=70,height=30)
        self.img_WS9 = Label(self.root,image=self.img_dark,borderwidth=0)
        self.img_WS9.place(x=500,y=610)
        self.img_WS9_ttp = tooltip.CreateToolTip(self.img_WS9, '')

        self.label_source10=tk.Label(self.root)
        self.label_source10.place(x=100,y=640,width=121,height=30)
        self.sourceEntry10=tk.Entry(self.root)
        self.sourceEntry10.place(x=220,y=640,width=200,height=30)
        self.chk_WS10=tk.Checkbutton(self.root)
        self.chk_WS10.place(x=425,y=640,width=70,height=30)
        self.img_WS10 = Label(self.root,image=self.img_dark,borderwidth=0)
        self.img_WS10.place(x=500,y=645)
        self.img_WS10_ttp = tooltip.CreateToolTip(self.img_WS10, '')

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

        self.update_ping_light(self.img_WS1, self.img_WS1_ttp, 0)
        self.update_ping_light(self.img_WS2, self.img_WS2_ttp, 0)
        self.update_ping_light(self.img_WS3, self.img_WS3_ttp, 0)
        self.update_ping_light(self.img_WS4, self.img_WS4_ttp, 0)
        self.update_ping_light(self.img_WS5, self.img_WS5_ttp, 0)
        self.update_ping_light(self.img_WS6, self.img_WS6_ttp, 0)
        self.update_ping_light(self.img_WS7, self.img_WS7_ttp, 0)
        self.update_ping_light(self.img_WS8, self.img_WS8_ttp, 0)
        self.update_ping_light(self.img_WS9, self.img_WS9_ttp, 0)
        self.update_ping_light(self.img_WS10,self.img_WS10_ttp,0)



    def populateWindow(self):
        #Window
        self.root.title("Workstation Data Recorder - Version " + self.config.get('version_info','versionNumber'))
        width=934
        height=780
        screenwidth = self.root.winfo_screenwidth()
        screenheight = self.root.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.root.geometry(alignstr)
        self.root.resizable(width=False, height=False)
        self.root.config(bg= "#383838")

        self.label_SwTitle=tk.Label(self.root)
        self.label_SwTitle["anchor"] = "center"
        self.label_SwTitle["bg"] = "#383838"
        ft = tkFont.Font(family='Verdana',size=-32)
        self.label_SwTitle["font"] = ft
        self.label_SwTitle["fg"] = "#79a878"
        self.label_SwTitle["justify"] = "center"
        self.label_SwTitle["text"] = "WORKSTATION DATA RECORDER"
        self.label_SwTitle.place(x=195,y=20,width=560,height=75)

        #Status frame
        self.statusFrame = tk.Frame(self.root)
        self.statusFrame["background"] = "dark gray"
        self.statusFrame.place(x=505,y=120,height=200,width=380)
        self.label_stats = tk.Label(self.statusFrame)
        self.label_stats["background"] = "dark gray"
        self.label_stats.place(x=143,y=5)
        self.label_stats["text"]= "DCP STATUS"
        self.label_stats["justify"]= "center"
        self.label_stats["fg"]= "dark blue"

        video_storage = DriveManager.get_video_storage_stats(g.paths['viddir']) #TODO: Add current session name to GUI.
        DriveManager.print_drive_stats(video_storage)

        self.label_HDD_Message_A = tk.Label(self.statusFrame)
        self.label_HDD_Message_A["background"] = "dark gray"
        self.label_HDD_Message_A.place(x=35,y=85)
        self.label_HDD_Message_A["fg"] = "dark red"
        self.label_HDD_Message_Overwrite_A = tk.Label(self.statusFrame)
        self.label_HDD_Message_Overwrite_A["background"] = "dark gray"
        self.label_HDD_Message_Overwrite_A.place(x=195,y=85)
        self.label_HDD_Message_Overwrite_A["fg"] = "dark red"


        self.label_HDD_Message_B = tk.Label(self.statusFrame)
        self.label_HDD_Message_B["background"] = "dark gray"
        self.label_HDD_Message_B.place(x=35,y=170)
        self.label_HDD_Message_B["fg"] = "dark red"
        self.label_HDD_Message_Overwrite_B = tk.Label(self.statusFrame)
        self.label_HDD_Message_Overwrite_B["background"] = "dark gray"
        self.label_HDD_Message_Overwrite_B.place(x=195,y=170)
        self.label_HDD_Message_Overwrite_B["fg"] = "dark red"

        #TODO: This can be added to the drive status message while recording over a full disk.
        # self.label_HDD_Message_Overwrite_A['text']= " Overwriting Data."
        # self.label_HDD_Message_Overwrite_B['text']= " Overwriting Data."

        self.label_HDD_Status = tk.Label(self.statusFrame)
        self.label_HDD_Status["background"] = "dark gray"
        self.label_HDD_Status.place(x=35,y=35)
        self.label_HDD_Status["fg"] = "black"
        self.label_HDD_Status["text"]= f"Disk A - Total Capacity: "


        self.label_Percent_Status_A = tk.Label(self.statusFrame)
        self.label_Percent_Status_A["background"] = "dark gray"
        self.label_Percent_Status_A["fg"] = "black"
        self.label_Percent_Status_A.place(x=35,y=60)

        self.label_HDD_Space = tk.Label(self.statusFrame)
        self.label_HDD_Space["background"] = "dark gray"
        self.label_HDD_Space["fg"] = "black"
        self.label_HDD_Space.place(x=205,y=35)
        self.Active_Image = Label(self.statusFrame,image=self.img_green,borderwidth=0) #TODO: Adjust image to remove background.
        self.Active_TTP = tooltip.CreateToolTip(self.Active_Image, 'Active')
        self.Inactive_Image = Label(self.statusFrame,image=self.img_dark,borderwidth=0)
        self.Inactive_TTP = tooltip.CreateToolTip(self.Inactive_Image, 'Inactive')
        self.label_Active_HDD = tk.Label(self.statusFrame)
        self.label_Active_HDD["text"] = "(Active)"
        self.label_Active_HDD["background"] = "dark gray"
        self.label_Active_HDD["fg"] = "dark green"

        self.label_HDD_Status_2 = tk.Label(self.statusFrame)
        self.label_HDD_Status_2["background"] = "dark gray"
        self.label_HDD_Status_2.place(x=35,y=120)
        self.label_HDD_Status_2["fg"] = "black"

        self.label_Percent_Status_B = tk.Label(self.statusFrame)
        self.label_Percent_Status_B["background"] = "dark gray"
        self.label_Percent_Status_B["fg"] = "black"
        self.label_Percent_Status_B.place(x=35,y=145)

        self.label_HDD_Status_2["text"]= f"Disk B - Total Capacity: "
        self.label_HDD_Space_2 = tk.Label(self.statusFrame)
        self.label_HDD_Space_2["background"] = "dark gray"
        self.label_HDD_Space_2["fg"] = "black"
        self.label_HDD_Space_2.place(x=205,y=120)

        self.diskLabelList_Warning = [self.label_HDD_Message_A,
                                      self.label_HDD_Message_B]

        self.diskLabelList_Overwrite = [self.label_HDD_Message_Overwrite_A,
                                        self.label_HDD_Message_Overwrite_B]

        self.diskLabelList_Space = [self.label_HDD_Space,
                                    self.label_HDD_Space_2]

        self.diskLabelList_Percent = [self.label_Percent_Status_A,
                                      self.label_Percent_Status_B,]

        if(video_storage[0]['active']):
            self.label_Active_HDD.place(x = 300,y=35)
            self.Active_Image.place(x=5,y=35) #TODO: Need to create a new image for the event frame. Background color issue. This should work otherwise.
            self.Inactive_Image.place(x=5,y=120)
        elif(video_storage[1]['active']):
            self.label_Active_HDD.place(x = 300,y=120)
            self.Active_Image.place(x=5,y=120)
            self.Inactive_Image.place(x=5,y=35)

        for i,drive_info in enumerate(video_storage):
            if drive_info['actual_pct_used_breach']: # bad bad bad over the limit
                self.diskLabelList_Space[i]["fg"] = "dark red"
                self.diskLabelList_Warning[i]['text']= "Disk At Capacity Limit."
            elif drive_info['actual_pct_used_warning']: # warning
                self.diskLabelList_Space[i]["fg"] = "#e0d900"

            freespace = utils.bytesto(drive_info['stats'].free,'gb')
            storage_text = f"{freespace:.2f} GB"
            self.diskLabelList_Space[i]["text"] = storage_text

            capacity_text = f'  {drive_info["actual_pct_used"]*100:.2f}% Used of {utils.bytesto(drive_info["actual_capacity"],"gb"):.2f} GB Available Space'
            self.diskLabelList_Percent[i]["text"] = capacity_text


        #Menu bar
        menubar = Menu(self.root, background='#ff8000', foreground='black', activebackground='gray', activeforeground='black')
        file = Menu(menubar, tearoff=0)
        if(g.dev_opts['includePlayback']):
            #TODO: Obsolete. Playback will be a fully separate app.
            file.add_command(label="Open Playback", command= lambda: self.openPlayback(playbackGUI))
            file.add_separator()
        file.add_command(label="Ping RNAs", command= self.ping_rnas)
        file.add_separator()
        file.add_command(label="Exit", command= self.root.quit)
        menubar.add_cascade(label="File", menu=file)
        self.root.config(menu=menubar)

        #Filepath/Directory Label and Display
        self.label_SaveDest=tk.Label(self.root)
        self.label_SaveDest["activebackground"] = "#383838"
        self.label_SaveDest["anchor"] = "w"
        self.label_SaveDest["bg"] = "#383838"
        ft = tkFont.Font(family='Verdana',size=-14)
        self.label_SaveDest["font"] = ft
        self.label_SaveDest["fg"] = "light gray"
        self.label_SaveDest["justify"] = "center"
        self.label_SaveDest["text"] = "Save Directory: "
        self.label_SaveDest.place(x=100,y=120,width=121,height=30)

        self.entry_SaveDir=tk.Entry(self.root)
        self.entry_SaveDir["borderwidth"] = "1px"
        ft = tkFont.Font(family='Verdana',size=-14)
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
        self.stopWatch = Stopwatch.StopWatch(self.root) #TODO: Put stopwatch in Vidrecorder and provide the number in a GUI update.
        self.stopWatch.place(x=275,y=165, width=75,height=30)

        #Record Button
        self.button_Record=tk.Button(self.root)
        self.button_Record["bg"] = "#efefef"
        ft = tkFont.Font(family='Verdana',size=-14)
        self.button_Record["font"] = ft
        self.button_Record["fg"] = "#000000"
        self.button_Record["justify"] = "center"
        self.button_Record["text"] = "Record"
        self.button_Record.place(x=355,y=165,width=145,height=30)
        self.button_Record["command"] = self.toggleRecord

        #All checkbox
        self.bool_checkedAllWorkstations = BooleanVar() #TODO: Obsolete. All available/connected WS's will record.
        self.WS_All=tk.Checkbutton(self.root)
        ft = tkFont.Font(family='Verdana',size=-14)
        self.WS_All["font"] = ft
        self.WS_All["fg"] = "light gray"
        self.WS_All["background"] = "#383838"
        self.WS_All["justify"] = "center"
        self.WS_All["text"] = "ALL"
        self.WS_All["offvalue"] = False
        self.WS_All["onvalue"] = True
        self.WS_All["variable"] = self.bool_checkedAllWorkstations
        self.WS_All["command"] = self.checkAllWorkstations
        self.WS_All.place(x=425,y=295,width=70,height=25)

        #Duration
        self.chk_Duration = tk.Checkbutton() #TODO: Obsolete.
        ft = tkFont.Font(family='Verdana',size=-14)
        self.chk_Duration["font"] = ft
        self.chk_Duration["justify"] = "center"
        self.chk_Duration["text"] = "  DURATION (m)"
        self.chk_Duration["offvalue"] = False
        self.chk_Duration["onvalue"] = True
        self.chk_Duration["variable"] = self.bool_useDuration
        self.chk_Duration["command"] = self.toggleEntry_Duration
        # self.chk_Duration.place(x=235,y=205,width=150,height=25) # TODO: uncomment to add duration back to gui
        self.entry_duration = tk.Entry(self.root) #TODO: Obsolete
        self.entry_duration["borderwidth"] = "1px"
        ft = tkFont.Font(family='Verdana',size=-14)
        self.entry_duration["font"] = ft
        self.entry_duration["fg"] = "#333333"
        self.entry_duration["justify"] = "center"
        self.entry_duration["textvariable"] = self.duration
        # self.entry_duration.place(x=390,y=205,width=70,height=25) # TODO: uncomment to add duration back to gui

        #WS labels and ip display
        for idx,src in enumerate(self.ipAddresses):
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
            ft = tkFont.Font(family='Verdana',size=-14)
            lbl["font"] = ft
            lbl["fg"] = "light gray"
            lbl["justify"] = "center"
        for ent in self.sourceEntryList:
            idx = self.sourceEntryList.index(ent)
            ent["borderwidth"] = "1px"
            ft = tkFont.Font(family='Verdana',size=-14)
            ent["font"] = ft
            ent["fg"] = "#333333"
            ent["justify"] = "center"
            ent["textvariable"] = self.ipAddresses[idx]
            ent["state"] = DISABLED
        for chk in self.chkBoxList:
            idx = self.chkBoxList.index(chk)
            if idx < 10:
                txt = f"WS{idx+1:02}"
            else:
                txt = f"Sh{idx - 9:02}"
            ft = tkFont.Font(family='Verdana',size=-14)
            chk["text"] = txt
            chk["font"] = ft
            chk["fg"] = "#333333"
            chk["justify"] = "center"
            chk["offvalue"] = False
            chk["onvalue"] = True
            chk["variable"] = self.workstationBoolList[idx]

        self.createStatusLabels()

# Main
if __name__ == "__main__":
    root = tk.Tk()
    app = WorkstationDataRecorder_GUI(root)
    root.mainloop()
