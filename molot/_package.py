import logging
import sys


class ShutdownHandler(logging.Handler):
    """Logging handler that shuts down application at certain level."""

    def emit(self, record):
        logging.shutdown()
        sys.exit(1)


def setup_logging(level: int, shutdown: int = logging.NOTSET, **kwargs):
    """Set logging levels.

    Args:
        level (int): Minimum level to print in output.
        shutdown (int, optional): Level to shut down application. Defaults to logging.NOTSET.
    """
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=level,
        **kwargs,
    )
    if shutdown != logging.NOTSET:
        logging.getLogger().addHandler(ShutdownHandler(level=shutdown))


def get_version() -> str:
    """Retrieve version from _version.py file.

    Returns:
        str: Package version or "0.0.0" when file missing.
    """
    try:
        from ._version import __version__  # type: ignore

        return __version__
    except ModuleNotFoundError:
        logging.warning("No _version.py file")
        return "0.0.0"
