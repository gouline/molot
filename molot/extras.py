import subprocess
import sys
from typing import Optional


class ReturnCodeError(Exception):
    """Error for failed shell commands in piped mode."""

    def __init__(self, code: int, output: str):
        self.code = code
        self.output = output


def shell(command: str, piped: bool = False, sensitive: bool = False) -> Optional[str]:
    """Runs command in outer shell.

    Args:
        command (str): Raw command to run.
        piped (bool, optional): Returns output as string if true, otherwise prints in stdout. Defaults to False.
        sensitive (bool, optional): Control whether shell command is hidden from logs. Defaults to False.

    Raises:
        ReturnCodeError: Raised when command failed in piped mode.

    Returns:
        Optional[str]: Returns string output when piped, otherwise nothing.
    """

    pipe = subprocess.PIPE if piped else None

    # Allow arbitrary indentation of block strings
    command = "\n".join([x.lstrip() for x in command.split("\n")])

    if sensitive:
        print("+ Shell")
    else:
        print(f"+ Shell: {command}")

    p = subprocess.Popen(command, shell=True, stdout=pipe, stderr=pipe)
    out, err = p.communicate()

    if p.returncode != 0:
        if piped:
            raise ReturnCodeError(p.returncode, err.decode("utf-8"))
        sys.exit(p.returncode)

    return out.decode("utf-8") if piped else None
