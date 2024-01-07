import collections
import logging
import os
from dataclasses import dataclass
from typing import Callable, Deque, Dict, Iterable, List, Mapping, MutableSequence

from .errors import TargetCircularDependencyError, TargetNotFoundError


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
        self.arg_vals: Dict[str, str] = {}
        self.file_vals: Dict[str, str] = {}

    def clear(self):
        self.targets.clear()
        self.envargs.clear()
        self.arg_vals.clear()
        self.file_vals.clear()

    def envarg_val(self, name: str, masked: bool = False) -> str:
        """Fetches value for an environment argument from any possible source.

        Args:
            name (str): Unique name.
            masked (bool, optional): Mask if sensitive envarg. Defaults to False.

        Returns:
            str: Retrieved value (masked, if requested) or default.
        """

        arg = self.envargs[name]
        mask = "**********" if masked and arg.sensitive else None

        # P1: override passed via --arg
        if name in self.arg_vals:
            return mask or self.arg_vals[name]

        # P2: environment variable
        val = os.getenv(name)
        if val is not None:
            return mask or val

        # P3: properties file passed via envargs_file()
        if name in self.file_vals:
            return mask or self.file_vals[name]

        # P4: provided default
        return mask or arg.default

    def targets_by_group(self) -> Mapping[str, Iterable[Target]]:
        by_group: Dict[str, MutableSequence[Target]] = {}

        targets = list(self.targets.values())
        targets.sort(key=lambda x: (x.group.lower(), x.name.lower()))
        for t in targets:
            grouped = by_group.get(t.group, [])
            grouped.append(t)
            if t.group not in by_group:
                by_group[t.group] = grouped

        return by_group

    def targets_to_execute(self, targets: List[str]) -> MutableSequence[Target]:
        to_evaluate: Deque[str] = collections.deque()
        to_evaluate.extendleft(targets)
        evaluated: Dict[str, bool] = {}
        to_execute: Deque[Target] = collections.deque()
        while to_evaluate:
            name = to_evaluate[-1]
            if name not in self.targets:
                raise TargetNotFoundError(name)

            t = self.targets[name]
            logging.debug("Evaluating target %s", name)

            deps_satisfied = True
            for dname in reversed(t.depends):
                if dname not in evaluated or not evaluated[dname]:
                    to_evaluate.append(dname)
                    deps_satisfied = False

            if not deps_satisfied:
                if name in evaluated:
                    raise TargetCircularDependencyError(name)

                evaluated[name] = False
                continue

            if name not in evaluated or not evaluated[name]:
                to_execute.appendleft(t)

            evaluated[name] = True
            to_evaluate.pop()

        return to_execute
