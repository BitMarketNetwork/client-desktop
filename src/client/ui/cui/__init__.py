import logging
from . import console
log = logging.getLogger(__name__)

def run(gcd):
    root = console.Console(gcd)
    if not root.read_config():
        log.warning("No config file detected")
    return root