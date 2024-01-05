import logging

from molot.package import setup_logging

from .test_core import *
from .test_helpers import *

setup_logging(level=logging.DEBUG, force=True)
