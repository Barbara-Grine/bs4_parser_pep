import argparse
import logging
from logging.handlers import RotatingFileHandler

from constants import BASE_DIR

LOG_FORMAT = '%(asctime)s - [%(levelname)s] - %(message)s'
DT_FORMAT = '%d.%m.%Y %H:%M:%S'

OUTPUT_PRETTY = 'pretty'
OUTPUT_FILE = 'file'
OUTPUT_CHOICES = (OUTPUT_PRETTY, OUTPUT_FILE)

OUTPUT_HELP = 'Дополнительные способы вывода данных'

LOG_DIR = BASE_DIR / 'logs'
LOG_FILE = LOG_DIR / 'parser.log'
MAX_LOG_BYTES = 10 ** 6
BACKUP_COUNT = 5


def configure_argument_parser(available_modes):
    parser = argparse.ArgumentParser(description='Парсер документации Python')
    parser.add_argument(
        'mode',
        choices=available_modes,
        help='Режимы работы парсера'
    )
    parser.add_argument(
        '-c',
        '--clear-cache',
        action='store_true',
        help='Очистка кеша'
    )
    parser.add_argument(
        '-o',
        '--output',
        choices=OUTPUT_CHOICES,
        help=OUTPUT_HELP
    )
    return parser


def configure_logging():
    LOG_DIR.mkdir(exist_ok=True)
    rotating_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_LOG_BYTES,
        backupCount=BACKUP_COUNT
    )
    logging.basicConfig(
        datefmt=DT_FORMAT,
        format=LOG_FORMAT,
        level=logging.INFO,
        handlers=(rotating_handler, logging.StreamHandler())
    )
