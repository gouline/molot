import argparse
import io
import sys
from functools import reduce
from pathlib import Path
from typing import Callable, List, Optional, Union

from dotenv import load_dotenv

from ._package import get_version
from ._state import EnvArg, State, Target
from .errors import TargetCircularDependencyError, TargetNotFoundError

_sys = sys
_args = _sys.argv[1:]
_state = State()


def _list_targets_str() -> str:
    """Compiles list of targets into a string.

    Returns:
        str: Formatted list of targets.
    """

    out = io.StringIO()

    targets = _state.targets_by_group()
    if targets:
        print("available targets:", file=out)
        for group, grouped in targets.items():
            print(f"  {group}", file=out)
            for t in grouped:
                depends = f"(depends: {', '.join(t.depends)})" if t.depends else ""
                print(f"    {t.name} - {t.description} {depends}", file=out)

    if _state.envargs:
        print("\nenvironment arguments:", file=out)
        for name, arg in _state.envargs.items():
            print(
                f"  {name} - {arg.description} (default: {arg.default})",
                file=out,
            )

    return out.getvalue()


def _list_targets():
    """Prints list of targets to stdout."""
    print(_list_targets_str(), end="")


def _argument_parser(preparse: bool = False) -> argparse.ArgumentParser:
    """Common definition for CLI argument parser.

    Args:
        preparse (bool, optional): Pre-parse mode for dotenv files. Defaults to False.

    Returns:
        argparse.ArgumentParser: Parser instance.
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_list_targets_str(),
        add_help=not preparse,
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
    if not preparse:
        parser.add_argument(
            "targets",
            metavar="TARGET",
            type=str,
            nargs="*",
            help="target to execute",
            default=["list"],
        )
    return parser


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
    return _state.envarg_val(name)


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


def envargs_file(path: Union[str, Path], sep="=", comment_prefix="#"):
    """Reads environment arguments from file and save them as defaults.

    This expects a simple properties file of form:
        # Some comment
        KEY1 = VALUE1
        KEY2=VALUE2
        KEY3 = "VALUE3"

    Args:
        path (Union[str, Path]): Path to configuration file.
        sep (str, optional): Key-value separator. Defaults to "=".
        comment_prefix (str, optional): Line prefix to consider a comment. Defaults to "#".
    """

    if not Path(path).is_file():
        print(f"Envargs {path} not found")
        return

    # https://stackoverflow.com/a/31852401/818393
    with open(path, "rt", encoding="utf-8") as f:
        for line in f:
            ln = line.strip()
            if ln and not ln.startswith(comment_prefix):
                key_value = ln.split(sep, 1)
                if len(key_value) == 2:
                    key = key_value[0].strip()
                    value = key_value[1].strip().strip('"')
                    _state.file_vals[key] = value


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


def evaluate():
    """Evaluates targets and environment arguments.

    Call to evaluate() must be at the very end of your script!
    """

    print(f"→ Running Molot {get_version()}...")

    args = _argument_parser().parse_args(args=_args)

    try:
        to_execute = _state.targets_to_execute(args.targets)

        non_phony = reduce(lambda acc, t: acc or not t.phony, to_execute, False)
        if non_phony:
            print("environment:")
            for argname in _state.envargs:
                value = _state.envarg_val(argname, masked=True)
                print(f"  {argname}={value}")
            print()

        while to_execute:
            t = to_execute.pop()
            print("→ Executing target:", t.name)
            t.func()
    except TargetNotFoundError as e:
        print("Target not found:", e.name, "\n")
        _list_targets()
        _sys.exit(1)
    except TargetCircularDependencyError as e:
        print(f"Circular dependency detected when evaluating target {e.name}")
        _sys.exit(2)

    _sys.exit(0)


def _init():
    """Initializes internal state for defining targets and arguments."""

    _state.clear()

    args, _ = _argument_parser(preparse=True).parse_known_args(args=_args)

    if args.dotenv:
        for dotenv_path in args.dotenv:
            load_dotenv(dotenv_path=dotenv_path)

    if args.arg:
        for a in args.arg:
            key_value = a.split("=", 1)
            if len(key_value) == 2:
                _state.arg_vals[key_value[0]] = key_value[1]

    target(
        name="list",
        description="lists all available targets",
        group="<builtin>",
        _phony=True,
    )(_list_targets)


_init()
