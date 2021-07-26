import time
import tkinter
import tkinter.scrolledtext
import tkinter.messagebox
import threading
import collections
import os
import re
import csv
from tkinter import ttk

import sys
sys.path.append("../vidrecorder/PlaybackWindow_GUI.py")
import PlaybackWindow_GUI
sys.path.append("../vidrecorder/BookmarkHandler.py")
import libs.BookmarkHandler

class Message():
    """This class represents a single message taken from a log:

    timestamp - timestamp of the message

    tags - tags of the message. Useful for filtering

    contents - the text of the message

    source - the log the message came from

    """

    def __init__(self, timestamp, tags, contents, source):
          self.timestamp = timestamp
          self.tags = tags
          self.contents = contents
          self.source = source

class AbstractLogFile():
    def next_message(self):
        return None

    def jump_to_time(self, timestamp):
        return None

class BookmarksLogFile(AbstractLogFile):
    def __init__(self, filename):
        self.filename = filename
        self.source = "Custom Bookmarks"
        self.file = open(self.filename, "r")

    def next_message(self):
        line = self.file.readline()
        if (line == None):
            return None
        pieces = line.split(" - ")
        if len(pieces) != 3:
            return None
        if pieces[1].find(" ") != -1:
            tags = pieces[1].split(" ")
        else:
            tags = list()
            tags.append(pieces[1])
        contents = pieces[2]
        timestamp = time.strptime(pieces[0], "%d %B %Y %H:%M:%S")
        return Message(timestamp, tags, contents.rstrip(), self.source)

    def jump_to_time(self, timestamp):
        self.file.seek(0, os.SEEK_SET)
        while True:
            message = self.next_message()
            if (message is None):
                return None
            if (time.mktime(message.timestamp) - time.mktime(timestamp) >= 0):
                return message

class RTILogFile(AbstractLogFile):
    def __init__(self, filename):
        self.filename = filename
        self.source = "RTI"
        self.file = open(self.filename, "r")
        self.tags = list()
        first_line = self.file.readline()
        self.halves = first_line.split(", ")
        for half in self.halves:
            quarters = half.split(": ")
            self.tags.append(quarters[1].rstrip())
        self.reader = csv.DictReader(self.file)
        self.fieldnames = self.reader.fieldnames

    def next_message(self):
        row = None
        try:
            row = next(self.reader)
        finally:
            if row is None:
                return None
            timestamp = time.strptime(row["Timestamp"], "%a %B %d %H:%M:%S %Y")
            contents = ""
            first_iteration = True
            for key in row.keys():
                if (key != "Timestamp"):
                    if not first_iteration:
                        contents += ", "
                    contents += key + " = " + row.get(key)
                    if first_iteration:
                        first_iteration = False
            return Message(timestamp, self.tags, contents, self.source)

    def jump_to_time(self, timestamp):
        self.file.seek(0, os.SEEK_SET)
        first_line = self.file.readline()
        self.reader = csv.DictReader(self.file)
        while True:
            message = self.next_message()
            if (message is None):
                return None
            if (time.mktime(message.timestamp) - time.mktime(timestamp) >= 0):
                return message

class SyslogLogFile(AbstractLogFile):
    def __init__(self, filename):
        self.filename = filename
        self.source = "Syslog"
        self.file = open(self.filename, "r")

    def next_message(self):
        tags = list()
        line = self.file.readline()
        if (line == None):
            return None

        try:
            regex = re.compile(" +")
            pieces = regex.split(line)

            time_str = pieces[0] + " " + pieces[1] + " " + pieces[2]
            timestamp = time.strptime(time_str, "%B %d %H:%M:%S")

            tags.append(pieces[4][0:len(pieces[4]) - 1])
            tags.append(pieces[3])
            contents = " ".join(pieces[5:])
        except:
            return None

        return Message(timestamp, tags, contents.rstrip(), self.source)

    def jump_to_time(self, timestamp):
        self.file.seek(0, os.SEEK_SET)
        while True:
            message = self.next_message()
            if (message is None):
                return None
            if (time.mktime(message.timestamp) - time.mktime(timestamp) >= 0):
                return message

class MateoLogFile(AbstractLogFile):
    """This class represents a log file for a Mateo-formatted log:

    __init__(self, filename) - For a given filename,
    this function outputs Message objects for every message
    contained within it.

    """
    def __init__(self, filename):
        self.filename = filename
        self.source = "Mateo"
        self.file = open(self.filename, "r")

    """

    Returns a Message object representing the next log message in the file.
    If the end of the file has been reached, it will return None.

    """
    def next_message(self):
        line = self.file.readline()
        if (line == None):
            return None
        pieces = line.split(" - ")
        if (len(pieces) != 3):
            return None
        tags = list()
        tags.append(pieces[1])
        contents = pieces[2]
        timestamp = time.strptime(pieces[0], "%d %B %Y %H:%M:%S")
        return Message(timestamp, tags, contents.rstrip(), self.source)

    def jump_to_time(self, timestamp):
        self.file.seek(0, os.SEEK_SET)
        while True:
            message = self.next_message()
            if (message is None):
                return None
            if (time.mktime(message.timestamp) - time.mktime(timestamp) >= 0):
                return message

class CanabalLogFile(AbstractLogFile):
    """This class represents a log file for a Canabal-formatted log:

    __init__(self, filename) - For a given filename,
    this function outputs Message objects for every message
    contained within it.

    """
    def __init__(self, filename):
        self.filename = filename
        self.source = "Canabal"
        self.file = open(self.filename, "r")

    """

    Returns a Message object representing the next log message in the file.
    If the end of the file has been reached, it will return None.

    """
    def next_message(self):
        line = self.file.readline()
        if (line == None):
            return None
        pieces = line.split(" yeet ")
        if (len(pieces) != 3):
            return None
        tags = list()
        tags.append(pieces[1])
        contents = pieces[2]
        timestamp = time.strptime(pieces[0], "%d %B %Y %H:%M:%S")
        return Message(timestamp, tags, contents.rstrip(), self.source)

    def jump_to_time(self, timestamp):
        self.file.seek(0, os.SEEK_SET)
        while True:
            message = self.next_message()
            if (message is None):
                return None
            if (time.mktime(message.timestamp) - time.mktime(timestamp) >= 0):
                return message


class LogPlayer(ttk.Notebook):
    def __init__(self, master=None, dir_path="raw_logs/", start_time = None, playback_gui = None):
        super().__init__(master)
        self.playback_gui = playback_gui
        self.given_start_time = start_time
        self.log_dir = dir_path
        self.master = master
        #self.pack()
        self.place(x=0,y=0,height=500,width=270)
        #self.place(x=0,y=0,height=175,width=1300)

        self.log_player_frame = tkinter.Frame(master=self)
        self.add(self.log_player_frame, text="Log Player")

        self.create_widgets()
        self.filtered_out = dict()
        self.messages_waiting_area = list()
        self.log_files = list()
        self.color_pairs = dict()
        self.events = None

        self.init_jump_to_event()

        self.bind('<<NotebookTabChanged>>', self.refresh_jump_to_event)

        self.select(1)

        self.first_bkmk_added = True

        self.print_messages_deque_lock = threading.Lock()

        self.initiate_logs()

    def sort_bookmarks(self):
        file = BookmarksLogFile(self.playback_gui.get_logs_dir() + "/bookmarks.txt")
        messages = list()
        while True:
            message = file.next_message()
            if message is not None:
                messages.append(message)
            else:
                break
        messages.sort(key=lambda message : time.mktime(message.timestamp))

        new_file = open(self.playback_gui.get_logs_dir() + "/bookmarks.txt", 'w')
        for message in messages:
            new_file.write(time.strftime("%d %B %Y %H:%M:%S", message.timestamp))
            new_file.write(" -")
            for tag in message.tags:
                new_file.write(" " + tag)
            new_file.write(" - ")
            new_file.write(message.contents + "\n")

    def refresh_bookmarks(self):
        self.sort_bookmarks()
        if self.first_bkmk_added:
            self.log_files.append(BookmarksLogFile(self.playback_gui.get_logs_dir() + "/bookmarks.txt"))
            self.first_bkmk_added = False
        self.forget(1)
        self.init_jump_to_event()

    def destroy(self):
        self.log_timer.cancel()
        self.clock_timer.cancel()
        self.log_timer.join()
        self.clock_timer.join()
        super().destroy()

    def fetch_next_message(self, timestamp = None):
        if timestamp is not None:
            self.messages_waiting_area.clear()
            for file in self.log_files:
                msg = file.jump_to_time(timestamp)
                if msg is not None:
                    self.messages_waiting_area.append(msg)
            self.messages_waiting_area.sort(key=lambda message : time.mktime(message.timestamp))
            try:
                lucky_message = self.messages_waiting_area[0]
                del self.messages_waiting_area[0]
            except:
                return None
            return lucky_message
        else:
            for file in self.log_files:
                msg = file.next_message()
                if msg is not None:
                    self.messages_waiting_area.append(msg)
            self.messages_waiting_area.sort(key=lambda message : time.mktime(message.timestamp))
            try:
                lucky_message = self.messages_waiting_area[0]
                del self.messages_waiting_area[0]
            except:
                return None
            return lucky_message


    def create_widgets(self):

        self.current_time_label = tkinter.Label(self.log_player_frame)
        self.current_time_label.pack(side="top")
        self.log_display = tkinter.scrolledtext.ScrolledText(self.log_player_frame)
        self.log_display.configure(state=tkinter.DISABLED)
        self.log_display.pack(side="bottom")
        self.filter_button = tkinter.Button(self.log_player_frame, text="Filter")
        self.filter_button.pack(side="left")
        self.filter_button.configure(command=self.filter_out_stuff)
        self.pause_play_button = tkinter.Button(self.log_player_frame, text="Pause")
        # self.pause_play_button.pack(side="left")
        self.pause_play_button.configure(command=self.pause_play)
        self.jump_to_time_button = tkinter.Button(self.log_player_frame, text="Jump To")
        self.jump_to_time_button.pack(side="right")
        self.jump_to_time_button.configure(command=self.jump_to_time)
        # self.jump_to_event_button = tkinter.Button(self.log_player_frame, text="Event Timeline")
        # self.jump_to_event_button.pack(side="right")
        # self.jump_to_event_button.configure(command=self.jump_to_event)
        # self.create_bookmark_button = tkinter.Button(self.log_player_frame, text="Create Bookmark")
        # self.create_bookmark_button.pack(side="right")
        # self.create_bookmark_button.configure(command=self.create_bookmark)
        self.playing = threading.Event()
        self.playing.set()
        self.jumping = threading.Event()

    def pause_play(self):
        # TODO: add code to pause/play video/audio !!This is done!!
        if (self.pause_play_button["text"] == "Pause"):
            self.pause_play_button.configure(text="Play")
            self.playing.clear()
        else:
            self.pause_play_button.configure(text="Pause")
            self.playing.set()

    def jump_to_time(self):
        jump_to_window = tkinter.Toplevel(master=self.log_player_frame)
        label = tkinter.Label(master=jump_to_window, text="Type in a timestamp with the following format: 12 April 2021 10:46:00")
        label.pack()
        text_var = tkinter.StringVar(master=jump_to_window)
        textbox = tkinter.Entry(master=jump_to_window, textvariable=text_var)
        textbox.pack()
        go_button = tkinter.Button(master=jump_to_window, text="Go")
        def go_button_handler(event):
            timestamp = None
            try:
                timestamp = time.strptime(text_var.get(), "%d %B %Y %H:%M:%S")
            except:
                tkinter.messagebox.showerror("Invalid Time Input", "Please follow the format for entering a timestamp.")
                jump_to_window.destroy()
                return
            try:
                self._jump_to_time(timestamp)
            finally:
                jump_to_window.destroy()
        go_button.bind('<Button-1>', go_button_handler)
        go_button.pack()
        jump_to_window.wm_resizable(False, False)
        jump_to_window.title("Jump To")
        jump_to_window.mainloop()

    def collect_event_values(self):
        # if self.events is not None:
        #     return

        self.events = list()

        local_log_files = list()

        list_of_log_files_in_folder = os.listdir(self.log_dir)
        for log_file_name in list_of_log_files_in_folder:
            if log_file_name.upper().startswith("MATEO"):
                local_log_files.append(MateoLogFile(self.log_dir + log_file_name))
            elif log_file_name.upper().startswith("CANABAL"):
                local_log_files.append(CanabalLogFile(self.log_dir + log_file_name))
            elif log_file_name.upper().startswith("SYSLOG"):
                local_log_files.append(SyslogLogFile(self.log_dir + log_file_name))
            elif log_file_name.upper().startswith("RTI"):
                local_log_files.append(RTILogFile(self.log_dir + log_file_name))
            elif log_file_name.upper().startswith("BOOKMARKS"):
                local_log_files.append(BookmarksLogFile(self.log_dir + log_file_name))

        for log_file in local_log_files:
            while True:
                message = log_file.next_message()
                if message is None:
                    break
                if (message.source, message.tags, message.timestamp) not in self.events:
                    self.events.append((message.source, message.tags, message.timestamp))

    def refresh_jump_to_event(self, event):
        for key in self.color_pairs.keys():
            self.event_tree.tag_configure(tagname=key, foreground=self.color_pairs.get(key))

    def init_jump_to_event(self):
        # jump_to_event = tkinter.Toplevel(master=self)

        self.jump_to_event_frame = tkinter.Frame(master=self)
        self.add(self.jump_to_event_frame, text="Event Timeline")

        self.event_tree = ttk.Treeview(master=self.jump_to_event_frame, selectmode='browse')

        source_iids = dict()
        tag_iids = dict()

        self.collect_event_values()

        if self.events is None:
            return
        if len(self.events) == 0:
            return

        self.events.sort(key=lambda event : time.mktime(event[2]))

        for event in self.events:
            source = event[0]
            tags = event[1]
            timestamp = event[2]

            if source not in source_iids.keys():
                iid = self.event_tree.insert("", "end", text=source, tags=(source))
                source_iids.update({source : iid})
                self.event_tree.tag_configure(tagname=source, foreground=self.color_pairs.get(source))

            for tag in tags:
                if tag not in tag_iids.keys():
                    iid = self.event_tree.insert(source_iids.get(source), "end", text=tag, tags=(tag))
                    tag_iids.update({tag : iid})
                    self.event_tree.tag_configure(tagname=tag, foreground=self.color_pairs.get(tag))
                self.event_tree.insert(tag_iids.get(tag), "end", text=time.strftime("%d %B %Y %H:%M:%S", (timestamp)))

        def tree_event_handler(event):
            timestamp = None
            try:
                timestamp = time.strptime(self.event_tree.item(self.event_tree.focus())["text"], "%d %B %Y %H:%M:%S")
            except:
                pass
            finally:
                if timestamp is not None:
                    threading.Thread(target=self._jump_to_time, args=(timestamp,)).start()
                    # self._jump_to_time(timestamp)
                    self.events = None
                    # jump_to_event.destroy()
        self.event_tree.bind('<<TreeviewSelect>>', tree_event_handler)

        self.vertical_scrollbar = tkinter.Scrollbar(master=self.jump_to_event_frame,orient=tkinter.VERTICAL,command=self.event_tree.yview)
        self.horizontal_scrollbar = tkinter.Scrollbar(master=self.jump_to_event_frame,orient=tkinter.HORIZONTAL,command=self.event_tree.xview)

        self.jump_to_event_frame.rowconfigure(0, weight=1)
        self.jump_to_event_frame.columnconfigure(0, weight=1)
        self.event_tree.grid(row = 0, column = 0, sticky=tkinter.N+tkinter.S+tkinter.E+tkinter.W)
        self.vertical_scrollbar.grid(row=0, column=1, sticky=tkinter.N+tkinter.S)
        self.horizontal_scrollbar.grid(row=1, column=0, sticky=tkinter.E+tkinter.W)
        self.event_tree["yscrollcommand"] = self.vertical_scrollbar.set
        self.event_tree["xscrollcommand"] = self.horizontal_scrollbar.set

        # jump_to_event.title("Jump To Event")
        # jump_to_event.mainloop()

    def _jump_to_time(self, timestamp):
        if self.playback_gui is not None:
            self.playback_gui.jump_to_time(timestamp)

        self.jumping.set()
        self.log_timer.cancel()
        if self.log_timer.is_alive():
            self.log_timer.join()
        message = self.fetch_next_message(timestamp=timestamp)

        with self.print_messages_deque_lock:
            self.messages_deque.clear()
        self.print_messages_deque()
        self.clock_timer.cancel()
        if self.clock_timer.is_alive():
            self.clock_timer.join()
        self.initiate_clock(timestamp)

        if message is None:
            return

        time_delta = time.mktime(message.timestamp) - time.mktime(timestamp)
        self.log_timer = threading.Timer(time_delta, self.update_logs, [message, timestamp])
        self.jumping.clear()
        self.log_timer.start()

    def update_clock(self):
        self.playing.wait()
        self.current_time = time.localtime(time.mktime(self.current_time) + 1)
        self.current_time_label.configure(text=time.strftime("%H:%M:%S", self.current_time))
        self.clock_timer = threading.Timer(1.0, self.update_clock)
        self.clock_timer.start()

    def initiate_clock(self, timestamp):
        self.current_time = timestamp
        self.current_time_label.configure(text=time.strftime("%H:%M:%S", self.current_time))
        self.clock_timer = threading.Timer(1.0, self.update_clock)
        self.clock_timer.start()

    def update_logs(self, message, last_timestamp):
        while (not self.playing.is_set()):
            time.sleep(0.01)
            if (self.jumping.is_set()):
                return

        if message is None:
            return

        while time.mktime(self.current_time) < time.mktime(message.timestamp):
            time.sleep(0.01)
            pass

        with self.print_messages_deque_lock:
            self.messages_deque.append(message)
        for tag in message.tags:
            if (tag not in self.filtered_out):
                self.filtered_out.update({tag : False})
        if (message.source not in self.filtered_out):
            self.filtered_out.update({message.source : False})
        self.print_messages_deque()

        # Get next message
        upcoming_message = self.fetch_next_message()
        if (upcoming_message is not None):
            time_delta = time.mktime(upcoming_message.timestamp) - time.mktime(message.timestamp)
            self.log_timer = threading.Timer(time_delta, self.update_logs, [upcoming_message, message.timestamp])
            self.log_timer.start()


    def filter_out_stuff(self):
        filter_window = tkinter.Toplevel(master=self)
        filter_window.title("Check items to filter")
        filter_window.minsize(width=250,height=80)

        categories_and_sources = list()
        vals = list()
        for key in self.filtered_out.keys():
            val = tkinter.IntVar(master=filter_window, value=(1 if self.filtered_out.get(key) else 0))
            checkbox = tkinter.Checkbutton(master=filter_window, variable=val, text=key, foreground = self.color_pairs.get(key))
            checkbox.bind('<Button-1>', self.apply_filter)
            categories_and_sources.append(checkbox)
            vals.append(val)

        for item in categories_and_sources:
            item.pack()
        close_button = tkinter.Button(master=filter_window, text="Close", command=filter_window.destroy)
        close_button.pack()

        filter_window.wm_resizable(False, False)
        filter_window.mainloop()

    def apply_filter(self, event):
        self.filtered_out.update({event.widget["text"] : not self.filtered_out.get(event.widget["text"])})
        self.print_messages_deque()

    def initiate_logs(self):
        self.messages_deque = collections.deque(maxlen=100)

        # Initiate log files

        list_of_log_files_in_folder = os.listdir(self.log_dir)
        for log_file_name in list_of_log_files_in_folder:
            if log_file_name.upper().startswith("MATEO"):
                self.log_files.append(MateoLogFile(self.log_dir + log_file_name))
            elif log_file_name.upper().startswith("CANABAL"):
                self.log_files.append(CanabalLogFile(self.log_dir + log_file_name))
            elif log_file_name.upper().startswith("SYSLOG"):
                self.log_files.append(SyslogLogFile(self.log_dir + log_file_name))
            elif log_file_name.upper().startswith("RTI"):
                self.log_files.append(RTILogFile(self.log_dir + log_file_name))
            elif log_file_name.upper().startswith("BOOKMARKS"):
                self.log_files.append(BookmarksLogFile(self.log_dir + log_file_name))

        # Get next message
        current_message = self.fetch_next_message()

        if self.given_start_time is None:
            self.initiate_clock(current_message.timestamp)
            self.log_timer = threading.Timer(0, self.update_logs, [current_message, current_message.timestamp])
            self.log_timer.start()
        else:
            self.initiate_clock(self.given_start_time)
            time_delta = time.mktime(current_message.timestamp) - time.mktime(self.given_start_time)
            self.log_timer = threading.Timer(time_delta, self.update_logs, [current_message, self.given_start_time])
            self.log_timer.start()

    def print_messages_deque(self):
        with self.print_messages_deque_lock:
            self.log_display.configure(state=tkinter.NORMAL)

            colors = collections.deque(("red", "green", "blue", "magenta", "#ffaf00", "#c800ff", "#2baed5", "#d99a26", "#2d627f"))
            self.color_pairs.clear()

            self.log_display.delete("1.0", tkinter.END)
            for message in self.messages_deque:
                if ((not self.filtered_out.get(message.source))):
                    break_out = False
                    for tag in message.tags:
                        break_out = break_out or self.filtered_out.get(tag)
                    if not break_out:
                        self.log_display.insert(tkinter.END, "\n")
                        self.log_display.insert(tkinter.END, time.asctime(message.timestamp), ("timestamp", time.asctime(message.timestamp)))
                        def handler(event, self=self, timestamp=message.timestamp):
                            return self._jump_to_time(timestamp)
                        self.log_display.tag_bind(time.asctime(message.timestamp), '<Button-1>', handler)
                        self.log_display.insert(tkinter.END, " - ")
                        self.log_display.insert(tkinter.END, message.source, (message.source))
                        self.log_display.insert(tkinter.END, " - ")
                        for tag in message.tags:
                            self.log_display.insert(tkinter.END, tag, (tag))
                            self.log_display.insert(tkinter.END, " - ")
                        self.log_display.insert(tkinter.END, message.contents, ("contents"))
                        self.log_display.insert(tkinter.END, "\n")

                if (message.source not in self.color_pairs):
                    self.color_pairs.update({message.source : colors[0]})
                    colors.rotate()

                for tag in message.tags:
                    if (tag not in self.color_pairs):
                        self.color_pairs.update({tag : colors[0]})
                        colors.rotate()

                self.log_display.tag_config(message.source, foreground=self.color_pairs.get(message.source))
                for tag in message.tags:
                    self.log_display.tag_config(tag, foreground=self.color_pairs.get(tag))

            self.log_display.tag_config("timestamp", background="black", foreground="white")

            self.log_display.yview_moveto(1.0)

            self.log_display.configure(state=tkinter.DISABLED)






# main code
if __name__ == "__main__":
    root = tkinter.Tk()
    app = LogPlayer(master=root)
    app.master.title("Log Player")
    app.master.wm_resizable(False, False)
    app.mainloop()