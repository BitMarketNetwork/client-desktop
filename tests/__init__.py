import logging
from pathlib import Path
import sys

logging.basicConfig(
    format='[%(levelname)s]<[%(threadName)s> %(name)s[%(funcName)s:%(lineno)s]: %(message)s',
    # datefmt='%Y-%m-%d %H:%M:%S %z',
    style='%',
    level=logging.DEBUG,
    stream=sys.stdout)
DATA_PATH = Path(__file__).parent.resolve() / "data"
TEST_DATA_PATH = DATA_PATH
