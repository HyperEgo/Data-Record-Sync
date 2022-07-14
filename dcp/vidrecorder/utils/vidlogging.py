import logging
import sys
import os
import pwd
import grp
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
            self._setGroup(self.baseFilename)
            self._setPermissions(self.baseFilename,self.permission)

    def doRollover(self):
        # Rotate the file first
        RotatingFileHandler.doRollover(self)

        self._setGroup(self.baseFilename)
        self._setPermissions(self.baseFilename,self.permission)

    def _setGroup(self,path):
        fileutils.set_group(self.baseFilename,group=self.group)

    def _setPermissions(self,path,octval):
        fileutils.set_permissions(self.baseFilename,octval=self.permission)


def _try_set_permissions(filepath,permissions):
    try:
        fileutils.set_permissions(filepath,permissions)
    except:
        print(f"Failed trying to change permissions on existing path: {filepath}")

def _create_logdir(log_dir, log_group, log_permissions):

    success = False
    # If log_dir exists move on
    if os.path.exists(log_dir):
        _try_set_permissions(log_dir,log_permissions)
        return success

    # Create the log directory if dne
    try:
        fileutils.dcp_mkdir(log_dir,log_group,log_permissions)
        success = True
    except:
        success = False

    return success

def init_logs(log_dir, log_group, log_permissions):
    print('Initializing logs ...')
    success = _create_logdir(log_dir, log_group, log_permissions)
    if not success:
        log_dir = os.path.join(g.paths['exedir'],'logs') # dev version
        success = _create_logdir(log_dir, log_group, log_permissions)
        if not success:
            print('ERROR: Log Directory Creation Failure') # TODO: handle this error gracefully
            return

    g.paths['logs'] = log_dir
    g.paths['logfile'] = os.path.join(g.paths['logs'],'dcp.log')
    g.paths['errfile'] = os.path.join(g.paths['logs'],'err.log')
    g.log['dir'] = log_dir
    g.log['group'] = log_group
    g.log['permissions'] = log_permissions
    g.log['logfile'] = g.paths['logfile']
    g.log['errfile'] = g.paths['errfile']

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







# import logging
# import sys
# from logging.handlers import RotatingFileHandler
# FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# class VidLogger:
#     """Class that handles all logging in vidrecorder app"""

#     def __init__(self, abs_log_file, formatter=FORMATTER):
#         self.formatter = formatter
#         self.log_file = abs_log_file

#     def get_console_handler(self):
#         console_handler = logging.StreamHandler(sys.stdout)
#         console_handler.setFormatter(FORMATTER)
#         return console_handler

#     def get_file_handler(self):
#         file_handler = RotatingFileHandler(self.log_file, mode='a', maxBytes=5*1024*1024,
#                                         backupCount=2, encoding=None, delay=0)
#         file_handler.setFormatter(FORMATTER)
#         return file_handler

#     def get_logger(self,logger_name,logging_level=logging.DEBUG,handlers='both_console_and_file'):
#         logger = logging.getLogger(logger_name)
#         logger.setLevel(logging_level)
#         if handlers == 'both_console_and_file':
#             logger.addHandler(self.get_console_handler())
#             logger.addHandler(self.get_file_handler())
#         elif handlers == 'console_only':
#             logger.addHandler(self.get_console_handler())
#         elif handlers == 'file_only':
#             logger.addHandler(self.get_file_handler())

#         # with this pattern, it's rarely necessary to propogate the error up to parent
#         logger.propagate = False
#         return logger

# if __name__ == "__main__":
#     log_file = 'test.log'
#     vidlogger = VidLogger(log_file)
#     logger = vidlogger.get_logger("BLUBBLUB")
#     logger.debug("Does this work?")
#     logger2 = vidlogger.get_logger("BLUBBLUB2")
#     logger3 = vidlogger.get_logger("BLUBBLUB2")
#     print(logger == logger2)
#     print(logger2 == logger3)
#     logger2.debug("Does this work?")
    