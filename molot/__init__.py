import argparse
import collections
import io
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Deque, Dict, List, Optional

from .package import ReturnCodeError, get_version, logging_levels
from .state import EnvArg, State, Target

logging_levels(show=logging.INFO, shutdown=logging.CRITICAL)

__version__ = get_version()

# Return codes
SUCCESS = 0
TARGET_NOT_FOUND = 1
CIRCULAR_DEPENDENCY = 2

PROJECT_PATH = Path(sys.argv[0]).absolute().parent

_state = State()


def target(
    name: Optional[str] = None,
    description: Optional[str] = None,
    group: Optional[str] = None,
    depends: Optional[List[str]] = None,
    _phony: bool = False,
) -> Callable:
    """Decorator for executable targets.

    Args:
        name (Optional[str], optional): Unique name (function name used by default). Defaults to None.
        description (Optional[str], optional): Human-readable description to display in the help message. Defaults to None.
        group (Optional[str], optional): Grouping to display under in the help message. Defaults to None.
        depends (Optional[List[str]], optional): List of dependency target names. Defaults to None.
        _phony (bool, optional): Determines whether target is a phony and doesn't use environment. Defaults to False.

    Returns:
        Callable: Decorator function.
    """

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        tname = name or func.__name__
        _state.targets[tname] = Target(
            name=tname,
            description=description or "<no description>",
            group=group or "<ungrouped>",
            depends=depends or [],
            phony=_phony,
            func=func,
        )
        return wrapper

    return decorator


def _list_targets_str() -> str:
    """Compiles list of targets into a string.

    Returns:
        str: Formatted list of targets.
    """

    out = io.StringIO()

    targets = list(_state.targets.values())
    if len(targets) > 0:
        print("available targets:", file=out)
        targets.sort(key=lambda x: (x.group.lower(), x.name.lower()))
        targets_group = None
        for t in targets:
            depends = f"(depends: {', '.join(t.depends)})" if t.depends else ""
            if targets_group != t.group:
                targets_group = t.group
                print(f"  {t.group}", file=out)
            print(f"    {t.name} - {t.description} {depends}", file=out)

    if len(_state.envargs) > 0:
        print("\nenvironment arguments:", file=out)
        for aname in _state.envargs:
            arg = _state.envargs[aname]
            print(
                f"  {arg.name} - {arg.description} (default: {arg.default})",
                file=out,
            )

    return out.getvalue()


@target(
    name="list",
    description="lists all available targets",
    group="<builtin>",
    _phony=True,
)
def _list_targets():
    print(_list_targets_str(), end="")


def _envargval(name: str, default: str) -> str:
    # P1: override passed via --arg
    if name in _state.envarg_vals_override:
        return _state.envarg_vals_override[name]

    # P2: environment variable
    val = os.getenv(name)
    if val is not None:
        return val

    # P3: properties file passed via envargs_file()
    if name in _state.envarg_vals_base:
        return _state.envarg_vals_base[name]

    # P4: provided default
    return default


def envarg(
    name: str,
    default: str = "",
    description: Optional[str] = None,
    sensitive: bool = False,
) -> str:
    """Environment argument with string value.

    Args:
        name (str): Unique name.
        default (str, optional): Default value when not set. Defaults to "".
        description (Optional[str], optional): Human-readable description to display in the help message. Defaults to None.
        sensitive (bool, optional): Sensitive value that will be masked in output. Defaults to False.

    Returns:
        str: Retrieved value or default.
    """
    _state.envargs[name] = EnvArg(
        name=name,
        description=description or "<no description>",
        default=default,
        sensitive=sensitive,
    )
    return _envargval(name, default)


def envarg_bool(
    name: str,
    default: bool = False,
    description: Optional[str] = None,
) -> bool:
    """Environment argument with boolean value.

    Args:
        name (str): Unique name.
        default (bool, optional): Default value when not set. Defaults to False.
        description (Optional[str], optional): Human-readable description to display in the help message. Defaults to None.

    Returns:
        bool: Retrieved value or default.
    """
    v = envarg(name, str(default), description)
    return v.lower() == "true"


def envarg_int(
    name: str,
    default: int = 0,
    description: Optional[str] = None,
) -> int:
    """Environment argument with integer value.

    Args:
        name (str): Unique name.
        default (int, optional): Default value when not set. Defaults to 0.
        description (Optional[str], optional): Human-readable description to display in the help message. Defaults to None.

    Returns:
        int: Retrieved value or default.
    """
    v = envarg(name, str(default), description)
    if not v.isdecimal():
        raise ValueError(f"invalid integer envarg {name}: {v}")
    return int(v)


def envargs_file(path: str, sep="=", comment_prefix="#"):
    """Reads environment arguments from file and save them as defaults.

    This expects a simple properties file of form:
        # Some comment
        KEY1 = VALUE1
        KEY2=VALUE2
        KEY3 = "VALUE3"

    Args:
        path (str): Path to configuration file.
        sep (str, optional): Key-value separator. Defaults to "=".
        comment_prefix (str, optional): Line prefix to consider a comment. Defaults to "#".
    """

    if not Path(path).is_file():
        print(f"Envargs {path} not found")
        return

    # https://stackoverflow.com/a/31852401/818393
    with open(path, "rt", encoding="utf-8") as f:
        for line in f:
            l = line.strip()
            if l and not l.startswith(comment_prefix):
                key_value = l.split(sep)
                key = key_value[0].strip()
                value = sep.join(key_value[1:]).strip().strip('"')

                if key not in _state.envarg_vals_base:
                    _state.envarg_vals_base[key] = value


def evaluate(_suppress_exit: bool = False) -> int:
    """Evaluates targets and environment arguments.

    Call to evaluate() must be at the very end of your script!
    """

    code = SUCCESS

    print(f"→ Running Molot {__version__}...")

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_list_targets_str(),
    )
    parser.add_argument(
        "targets",
        metavar="TARGET",
        type=str,
        nargs="*",
        help="target to execute",
        default=["list"],
    )
    parser.add_argument(
        "--arg",
        metavar="KEY=VALUE",
        nargs="*",
        help="overwrite environment arguments",
    )
    parser.add_argument(
        "--dotenv",
        metavar="PATH",
        type=str,
        nargs="*",
        help="path to .env file to load",
    )
    args = parser.parse_args()

    to_evaluate: Deque[str] = collections.deque()
    to_evaluate.extendleft(args.targets)
    evaluated: Dict[str, bool] = {}
    to_execute: Deque[Target] = collections.deque()
    while len(to_evaluate) > 0:
        name = to_evaluate[-1]
        if name not in _state.targets:
            code = TARGET_NOT_FOUND
            print("Target not found:", name, "\n")
            _list_targets()
            break

        t = _state.targets[name]
        logging.debug("Evaluating target %s", name)

        deps_satisfied = True
        for dname in reversed(t.depends):
            if dname not in evaluated or not evaluated[dname]:
                to_evaluate.append(dname)
                deps_satisfied = False

        if not deps_satisfied:
            if name in evaluated:
                code = CIRCULAR_DEPENDENCY
                print(f"Circular dependency detected when evaluating target {name}")
                return code if _suppress_exit else sys.exit(code)

            evaluated[name] = False
            continue

        if name not in evaluated or not evaluated[name]:
            to_execute.appendleft(t)

        evaluated[name] = True
        to_evaluate.pop()

    env_listed = False
    while len(to_execute) > 0:
        t = to_execute.pop()

        if not env_listed and not t.phony:
            print("environment:")
            for key, var in _state.envargs.items():
                value = _envargval(key, var.default)
                if value and var.sensitive:
                    value = "**********"
                print(f"  {key}={value}")
            print()
            env_listed = True

        print("→ Executing target:", t.name)
        t.func()

    return code if _suppress_exit else sys.exit(code)


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
