import os
import time
import threading
import multiprocessing

class FileMonitorError(Exception):
    """A custom exception used to report errors in use of FileMonitor class"""

class FileMonitor:
    """Monitors a file for state changes"""

    def __init__(self, filepath, hz=2, logger=print, update_callback=None):
        self.filepath = filepath
        self.logger = logger
        self.hz = hz
        self._file_monitor_process = None
        self.running = False
        self.update_callback = update_callback

    def start(self):
        """Start monitoring the file"""
        if self._file_monitor_process is None:
            # self._file_monitor_process = threading.Thread(target=self.check_file_loop)
            self._file_monitor_process = multiprocessing.Process(target=self.check_file_loop)
            self._file_monitor_process.daemon = True

        if self._file_monitor_process.is_alive():
            raise FileMonitorError(f"FileMonitor is running. Use .stop to stop it")

        self.running = True
        self._file_monitor_process.start()

    def stop(self):
        """Stop monitoring the file"""
        if not self._file_monitor_process.is_alive():
            raise FileMonitorError(f"FileMonitor is not running. Use .start to start it")

        self.running = False
        self._file_monitor_process.terminate()
        self._file_monitor_process.join()
        self.logger(f'{os.path.basename(self.filepath)} monitor process has been successfully terminated')
        self._file_monitor_process = None


    def check_file_loop(self):
        if self.logger:
            self.logger("-----------------------------------------")
            self.logger(f"Checking the file: {self.filepath} {self.hz} times per second\n")
        t = float(0)
        tinterval = 1.0/self.hz
        while(self.running):
            output = self.collect_file_stats(t)
            if self.logger:
                self.logger(output)
            time.sleep(tinterval)
            t += tinterval

    def collect_file_stats(self,t):
        if not os.path.exists(self.filepath):
            output = f"T: {t:.03} -- File: doesn't exist"
        else:
            output = f"T: {t:.03} -- File: {os.path.basename(self.filepath)} -- sz: {os.path.getsize(self.filepath)}"
        return output

