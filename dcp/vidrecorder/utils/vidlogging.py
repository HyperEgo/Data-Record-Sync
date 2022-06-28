import logging
import sys
import os
import pwd
import grp
from pathlib import Path
from logging.handlers import RotatingFileHandler

from global_vars import g
import utils.fileutils as fileutils


FILE_FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
CONSOLE_FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOG_FILE = 'default.log'

class RotatingFileHandlerWithPermissions(RotatingFileHandler):

    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0,
                 encoding=None, delay=False, group="ibcs", permission=0o777):

        super(RotatingFileHandlerWithPermissions,self).__init__(filename,mode,maxBytes,backupCount,encoding,delay)

        self.group = group
        self.permission = permission

        if os.path.isfile(self.baseFilename):
            file_info = Path(self.baseFilename)
            file_group = file_info.group()
            if file_group != self.group:
                self._setGroup(self.baseFilename)
            # self._setPermissions(self.baseFilename,self.permission)

    def doRollover(self):
        # Rotate the file first
        RotatingFileHandler.doRollover(self)

        self._setGroup(self.baseFilename)
        self._setPermissions(self.baseFilename,self.permission)

    def _setGroup(self,path):
        fileutils.set_group(self.baseFilename,group=self.group)

    def _setPermissions(self,path,octval):
        fileutils.set_permissions(self.baseFilename,octval=self.permission)


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CONSOLE_FORMATTER)
    return console_handler

def get_file_handler(filename=LOG_FILE):
    file_handler = RotatingFileHandlerWithPermissions(filename, mode='a', maxBytes=5*1024*1024,
                        backupCount=10, encoding=None, delay=0,
                        group=g.log['group'],permission=g.log['permissions'])
    file_handler.setFormatter(FILE_FORMATTER)
    return file_handler

def get_logger(logger_name,logging_level=logging.DEBUG,log_to_console=True,log_to_file=True,filename=LOG_FILE):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging_level)
    if log_to_console:
        logger.addHandler(get_console_handler())
    if log_to_file:
        logger.addHandler(get_file_handler(filename))

    # with this pattern, it's rarely necessary to propogate the error up to parent
    logger.propagate = False
    return logger

def test_logger(logger):
    logger.debug('debug message')
    logger.info('info message')
    logger.warning('warning message')
    logger.error('error message')
    logger.critical('critical message')
