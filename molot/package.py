import importlib.metadata
import logging
import sys


class ReturnCodeError(Exception):
    """Error for failed shell commands in piped mode."""

    def __init__(self, code: int, output: str):
        """Constructor.

        Arguments:
            code {int} -- Return code from shell.
            output {str} -- Text output of error.
        """

        self.code = code
        self.output = output


class ShutdownHandler(logging.Handler):
    """Logging handler that shuts down application at certain level."""

    def emit(self, record):
        logging.shutdown()
        sys.exit(1)


def logging_levels(show: int, shutdown: int = logging.NOTSET):
    """Set logging levels.

    Args:
        show (int): Minimum level to print in output.
        shutdown (int, optional): Level to shut down application. Defaults to logging.NOTSET.
    """
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=show)
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
        return "0.0.0-UNKONWN"
