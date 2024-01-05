from dataclasses import dataclass
from typing import Callable, Dict, List


@dataclass
class Target:
    """Target definition."""

    name: str
    description: str
    group: str
    depends: List[str]
    phony: bool
    func: Callable


@dataclass
class EnvArg:
    """Environment argument definition."""

    name: str
    description: str
    default: str
    sensitive: bool


class State:
    """Internal state definition."""

    def __init__(self):
        self.targets: Dict[str, Target] = {}
        self.envargs: Dict[str, EnvArg] = {}
        self.envarg_vals_base: Dict[str, str] = {}
        self.envarg_vals_override: Dict[str, str] = {}

    def clear(self):
        self.targets.clear()
        self.envargs.clear()
        self.envarg_vals_base.clear()
        self.envarg_vals_override.clear()
