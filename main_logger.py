import inspect
import logging
import os
import sys
import time
import traceback
from datetime import datetime

logger_name = 'tm'
logger_level = 'DEBUG'

formatter = logging.Formatter(fmt='"%(asctime)s","%(name)s","%(levelname)s","%(message)s"')
formatter.converter = time.gmtime

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(data_dir, exist_ok=True)
log_filepath = os.path.join(data_dir, logger_name + ".log")
file_handler = logging.FileHandler(log_filepath, mode='a')
file_handler.setLevel(level=logger_level)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(level=logger_level)
console_handler.setFormatter(formatter)

logger = logging.getLogger(logger_name)
logger.setLevel(level=logger_level)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("Starting Logger....")

def application_error_handler(e):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    frame = inspect.currentframe()
    caller_frame = frame.f_back
    exc_type, exc_value, exc_traceback = sys.exc_info()

    stack_trace = ''.join(traceback.format_tb(exc_traceback))
    error_details = {
        'timestamp': current_time,
        'error_type': exc_type.__name__,
        'error_message': str(exc_value),
        'file_name': caller_frame.f_code.co_filename,
        'function_name': caller_frame.f_code.co_name,
        'line_number': caller_frame.f_lineno,
        'stack_trace': stack_trace
    }

    logger.error("---------================== Detailed Error Report ==================---------")
    logger.error(f"Timestamp: {error_details['timestamp']}")
    logger.error(f"Error Type: {error_details['error_type']}")
    logger.error(f"Error Message: {error_details['error_message']}")
    logger.error(f"File Name: {error_details['file_name']}")
    logger.error(f"Function Name: {error_details['function_name']}")
    logger.error(f"Line Number: {error_details['line_number']}")
    logger.error("Stack Trace:")
    logger.error(error_details['stack_trace'])
    logger.error("---------================== End Error Report ==================---------")
    del frame
    del caller_frame

