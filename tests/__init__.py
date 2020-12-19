
import logging
import pathlib
import sys

logging.basicConfig(
    format='[%(levelname)s]<[%(threadName)s> %(name)s[%(funcName)s:%(lineno)s]: %(message)s',
    # datefmt='%Y-%m-%d %H:%M:%S %z',
    style='%',
    level=logging.DEBUG,
    stream=sys.stdout)
TEST_DATA_PATH = pathlib.Path(__file__).parent.joinpath("data")
