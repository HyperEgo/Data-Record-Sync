import logging
import sys
from logging.handlers import RotatingFileHandler
FILE_FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
CONSOLE_FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOG_FILE = 'test.log'

def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CONSOLE_FORMATTER)
    return console_handler

def get_file_handler(filename=LOG_FILE):
    file_handler = RotatingFileHandler(filename, mode='a', maxBytes=5*1024*1024,
                                    backupCount=2, encoding=None, delay=0)
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
    