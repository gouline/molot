# pylint: disable=protected-access
import logging
import os
from pathlib import Path
from typing import Optional

import pytest

import molot.core
from molot import envarg, envarg_bool, envarg_int, envargs_file, evaluate, target
from molot.errors import TargetCircularDependencyError, TargetNotFoundError


class MockSys:
    class ExitError(Exception):
        def __init__(self, status: int):
            self.status = status

    def exit(self, __status: Optional[int] = None):
        if __status is not None and __status != 0:
            raise self.ExitError(__status)


_sys = MockSys()


def setup_module():
    molot.core._sys = _sys
    assert "list" in molot.core._state.targets
    molot.core._init()
    assert "list" in molot.core._state.targets


def test_empty():
    args = []
    molot.core._args = args

    targets = molot.core._state.targets_to_execute([])
    target_names = [t.name for t in targets]  # deque is reversed
    assert target_names == []

    targets = molot.core._state.targets_by_group()
    assert list(targets.keys()) == ["<builtin>"]
    assert [t.name for t in targets["<builtin>"]] == ["list"]

    evaluate()


def test_happy():
    args = ["entry"]
    molot.core._args = args

    assert envarg("ARG_STR", default="") == ""
    assert envarg_int("ARG_INT", default=42) == 42
    assert envarg_bool("ARG_BOOL", default=True)

    assert "ARG_STR" in molot.core._state.envargs
    assert "ARG_INT" in molot.core._state.envargs
    assert "ARG_BOOL" in molot.core._state.envargs

    @target()
    def dep3():
        logging.debug("dep3")

    @target(depends=["dep3"])
    def dep4():
        logging.debug("dep4")

    @target(group="group1", depends=["dep3", "dep4"])
    def entry():
        logging.debug("entry")

    assert "dep3" in molot.core._state.targets
    assert "dep4" in molot.core._state.targets
    assert "entry" in molot.core._state.targets
    targets = molot.core._state.targets_to_execute(args)
    target_names = [t.name for t in targets]  # deque is reversed
    assert target_names == ["entry", "dep4", "dep3"]

    targets = molot.core._state.targets_by_group()
    assert list(targets.keys()) == ["<builtin>", "<ungrouped>", "group1"]
    assert [t.name for t in targets["<builtin>"]] == ["list"]
    assert [t.name for t in targets["<ungrouped>"]] == ["dep3", "dep4"]
    assert [t.name for t in targets["group1"]] == ["entry"]

    evaluate()


def test_envarg_file():
    envargs_file(Path("tests") / "fixtures" / "envargs.env")
    assert envarg("KEY1") == "Value1"
    assert envarg("KEY2") == "Value2"
    assert envarg_bool("KEY3")
    assert envarg_int("KEY4") == 4
    assert envarg("KEY5") == ""
    assert envarg("KEY6") == "Value6"
    assert envarg("KEY7") == "Value7"
    assert envarg("KEY8") == "Value8"
    assert envarg("KEY9") == "Value9"
    assert not envarg_bool("KEY9")
    with pytest.raises(ValueError):
        envarg_int("KEY9")
    assert envarg("KEY10") == ""


def test_envarg_priorities():
    molot.core._args = ["--arg", "KEY2=Value222"]
    os.environ["KEY2"] = "Value22"
    os.environ["KEY6"] = "Value66"
    molot.core._init()
    envargs_file(Path("tests") / "fixtures" / "envargs.env")
    assert envarg("KEY1") == "Value1"
    assert envarg("KEY2") == "Value222"
    assert envarg("KEY6") == "Value66"


def test_target_circular():
    args = ["entry"]
    molot.core._args = args

    @target(depends=["dep2"])
    def dep1():
        logging.debug("dep1")

    @target(depends=["dep1"])
    def dep2():
        logging.debug("dep2")

    @target(depends=["dep1", "dep2"])
    def entry():
        logging.debug("entry")

    assert "dep1" in molot.core._state.targets
    assert "dep2" in molot.core._state.targets
    assert "entry" in molot.core._state.targets
    with pytest.raises(TargetCircularDependencyError):
        molot.core._state.targets_to_execute(args)

    with pytest.raises(MockSys.ExitError):
        evaluate()


def test_target_rename():
    args = ["entry1"]
    molot.core._args = args

    @target(name="entry2")
    def entry1():
        logging.debug("entry")

    assert "entry2" in molot.core._state.targets
    molot.core._state.targets_to_execute(["entry2"])  # test contents

    assert "entry1" not in molot.core._state.targets
    with pytest.raises(TargetNotFoundError):
        molot.core._state.targets_to_execute(args)

    with pytest.raises(MockSys.ExitError):
        evaluate()
