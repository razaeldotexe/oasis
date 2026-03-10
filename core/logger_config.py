import logging
import colorlog
import os
from logging.handlers import RotatingFileHandler

def setup_logger():
    # Buat direktori logs jika belum ada
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Handler untuk Terminal (Berwarna)
    stream_handler = colorlog.StreamHandler()
    stream_handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s',
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        }
    ))

    # Handler untuk File (Persisten - Rotating 5MB)
    file_handler = RotatingFileHandler(
        'logs/bot.log', maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    logger = colorlog.getLogger('oasis')
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    
    return logger

logger = setup_logger()
