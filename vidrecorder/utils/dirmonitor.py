import os
import time
import threading
import multiprocessing

class DirMonitorError(Exception):
    """A custom exception used to report errors in use of DirMonitor class"""

class DirMonitor:
    """Monitors a directory for file state changes"""

    def __init__(self, dirpath, hz=2, logger=print, update_callback=None):
        self.dirpath = dirpath
        self.logger = logger
        self.hz = hz
        self._dir_monitor_process = None
        self.running = False
        self.update_callback = update_callback

    def start(self):
        """Start monitoring the directory"""
        if self._dir_monitor_process is None:
            self._dir_monitor_process = threading.Thread(target=self.check_dir_loop)
            # self._dir_monitor_process = multiprocessing.Process(target=self.check_dir_loop)
            self._dir_monitor_process.daemon = True

        if self._dir_monitor_process.is_alive():
            raise DirMonitorError(f"DirMonitor is running. Use .stop to stop it")

        self.running = True
        self._dir_monitor_process.start()

    def stop(self):
        """Stop monitoring the directory"""
        if not self._dir_monitor_process.is_alive():
            raise DirMonitorError(f'DirMonitor is not running. Use .start to start it')

        self.running = False
        # self._dir_monitor_process.terminate()
        self._dir_monitor_process.join()
        self.logger(f'{os.path.basename(self.dirpath)} monitor process has been successfully terminated')
        self._dir_monitor_process = None


    def check_dir_loop(self):
        if self.logger:
            self.logger("-----------------------------------------")
            self.logger(f"Checking the directory: {self.dirpath} {self.hz} times per second\n")
        t = float(0)
        tinterval = 1.0/self.hz
        while(self.running):

            # Collect stats about directory
            allstats = self.collect_file_stats(t)

            # Do something with stats
            if self.update_callback:
                self.update_callback(allstats)
            # if self.logger:
            #     self.logger("\n"+output)

            # Go to sleep until it's time to wake up and check again
            time.sleep(tinterval)
            t += tinterval

    def collect_file_stats(self,t):
        print('DirMonitor::collect_file_stats')
        pass

