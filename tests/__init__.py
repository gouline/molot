import logging

from molot._package import setup_logging
from tests.test_core import *
from tests.test_extras import *

setup_logging(level=logging.DEBUG, force=True)
