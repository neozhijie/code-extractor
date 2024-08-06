import logging
import sys
import os
import atexit
import time

# Global variables
log_file_path = None
file_handler = None
logger = None

def setup_logger():
    global log_file_path, file_handler, logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File handler
    log_file_path = os.path.join(os.getcwd(), 'app.log')
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def cleanup_log_file():
    global log_file_path, file_handler, logger
    if file_handler:
        logger.removeHandler(file_handler)
        file_handler.close()
    
    if log_file_path and os.path.exists(log_file_path):
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                os.remove(log_file_path)
                print(f"Removed log file: {log_file_path}")
                break
            except Exception as e:
                if attempt < max_attempts - 1:
                    print(f"Error removing log file (attempt {attempt + 1}): {e}")
                    time.sleep(0.5)
                else:
                    print(f"Failed to remove log file after {max_attempts} attempts: {e}")

logger = setup_logger()

# Register the cleanup function to be called on exit
atexit.register(cleanup_log_file)
