import argparse
from dataclasses import dataclass
from typing import Callable, Dict, List

from dotenv import load_dotenv


@dataclass
class Target:
    name: str
    description: str
    group: str
    depends: List[str]
    phony: bool
    func: Callable


@dataclass
class EnvArg:
    name: str
    description: str
    default: str
    sensitive: bool


class State:
    def __init__(self):
        self.targets: Dict[str, Target] = {}
        self.envargs: Dict[str, EnvArg] = {}
        self.envarg_vals_base = {}
        self.envarg_vals_override = {}

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--arg", nargs="*")
        parser.add_argument("--dotenv", nargs="*")
        args, _ = parser.parse_known_args()

        if args.dotenv:
            for dotenv_path in args.dotenv:
                load_dotenv(dotenv_path=dotenv_path)

        if args.arg:
            for a in args.arg:
                aparts = a.split("=", 1)
                if len(aparts) >= 2:
                    self.envarg_vals_override[aparts[0]] = aparts[1]
