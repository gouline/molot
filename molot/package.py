import importlib.metadata
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
    """Retrieve version from package metadata.

    Returns:
        str: Package version or "0.0.0-UNKNOWN" when unavailable.
    """
    try:
        return importlib.metadata.version("molot")
    except importlib.metadata.PackageNotFoundError:
        logging.warning("No version found in metadata")
        return "0.0.0"


version = get_version()
