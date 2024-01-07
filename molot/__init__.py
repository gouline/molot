import logging

from ._package import get_version, setup_logging
from .core import envarg, envarg_bool, envarg_int, envargs_file, evaluate, target
from .extras import shell

setup_logging(level=logging.INFO, shutdown=logging.CRITICAL)

__version__ = get_version()
__all__ = [
    "envarg",
    "envarg_bool",
    "envarg_int",
    "envargs_file",
    "evaluate",
    "target",
    "shell",
]
