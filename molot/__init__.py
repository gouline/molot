import logging

from .core import envarg, envarg_bool, envarg_int, envargs_file, evaluate, reset, target
from .extras import shell
from .package import setup_logging, version

setup_logging(level=logging.INFO, shutdown=logging.CRITICAL)

__version__ = version
__all__ = [
    "target",
    "envarg",
    "envarg_int",
    "envarg_bool",
    "envargs_file",
    "evaluate",
    "reset",
    "shell",
]
