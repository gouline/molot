import logging

from .core import ResultCode, envarg, envarg_bool, envarg_int, evaluate, reset, target
from .helpers import ReturnCodeError, shell
from .package import setup_logging, version

setup_logging(level=logging.INFO, shutdown=logging.CRITICAL)

__version__ = version
__all__ = [
    "ResultCode",
    "ReturnCodeError",
    "target",
    "envarg",
    "envarg_int",
    "envarg_bool",
    "evaluate",
    "reset",
    "shell",
]
