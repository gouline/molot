# pylint: disable=protected-access
import logging
import os
import unittest
from pathlib import Path
from typing import Optional

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


class TestCore(unittest.TestCase):
    def setUp(self):
        molot.core._sys = _sys
        self.assertIn("list", molot.core._state.targets)
        molot.core._init()
        self.assertIn("list", molot.core._state.targets)

    def test_empty(self):
        args = []
        molot.core._args = args

        targets = molot.core._state.targets_to_execute([])
        target_names = [t.name for t in targets]  # deque is reversed
        self.assertEqual([], target_names)

        targets = molot.core._state.targets_by_group()
        self.assertEqual(["<builtin>"], list(targets.keys()))
        self.assertEqual(["list"], [t.name for t in targets["<builtin>"]])

        evaluate()

    def test_happy(self):
        args = ["entry"]
        molot.core._args = args

        self.assertEqual("", envarg("ARG_STR", default=""))
        self.assertEqual(42, envarg_int("ARG_INT", default=42))
        self.assertEqual(True, envarg_bool("ARG_BOOL", default=True))

        self.assertIn("ARG_STR", molot.core._state.envargs)
        self.assertIn("ARG_INT", molot.core._state.envargs)
        self.assertIn("ARG_BOOL", molot.core._state.envargs)

        @target()
        def dep3():
            logging.debug("dep3")

        @target(depends=["dep3"])
        def dep4():
            logging.debug("dep4")

        @target(group="group1", depends=["dep3", "dep4"])
        def entry():
            logging.debug("entry")

        self.assertIn("dep3", molot.core._state.targets)
        self.assertIn("dep4", molot.core._state.targets)
        self.assertIn("entry", molot.core._state.targets)
        targets = molot.core._state.targets_to_execute(args)
        target_names = [t.name for t in targets]  # deque is reversed
        self.assertEqual(["entry", "dep4", "dep3"], target_names)

        targets = molot.core._state.targets_by_group()
        self.assertEqual(["<builtin>", "<ungrouped>", "group1"], list(targets.keys()))
        self.assertEqual(["list"], [t.name for t in targets["<builtin>"]])
        self.assertEqual(["dep3", "dep4"], [t.name for t in targets["<ungrouped>"]])
        self.assertEqual(["entry"], [t.name for t in targets["group1"]])

        evaluate()

    def test_envarg_file(self):
        envargs_file(Path("tests") / "fixtures" / "envargs.env")
        self.assertEqual("Value1", envarg("KEY1"))
        self.assertEqual("Value2", envarg("KEY2"))
        self.assertEqual(True, envarg_bool("KEY3"))
        self.assertEqual(4, envarg_int("KEY4"))
        self.assertEqual("", envarg("KEY5"))
        self.assertEqual("Value6", envarg("KEY6"))
        self.assertEqual("Value7", envarg("KEY7"))
        self.assertEqual("Value8", envarg("KEY8"))
        self.assertEqual("Value9", envarg("KEY9"))
        self.assertEqual(False, envarg_bool("KEY9"))
        self.assertRaises(ValueError, lambda: envarg_int("KEY9"))
        self.assertEqual("", envarg("KEY10"))

    def test_envarg_priorities(self):
        molot.core._args = ["--arg", "KEY2=Value222"]
        os.environ["KEY2"] = "Value22"
        os.environ["KEY6"] = "Value66"
        molot.core._init()
        envargs_file(Path("tests") / "fixtures" / "envargs.env")
        self.assertEqual("Value1", envarg("KEY1"))
        self.assertEqual("Value222", envarg("KEY2"))
        self.assertEqual("Value66", envarg("KEY6"))

    def test_target_circular(self):
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

        self.assertIn("dep1", molot.core._state.targets)
        self.assertIn("dep2", molot.core._state.targets)
        self.assertIn("entry", molot.core._state.targets)
        self.assertRaises(
            TargetCircularDependencyError,
            lambda: molot.core._state.targets_to_execute(args),
        )

        self.assertRaises(MockSys.ExitError, evaluate)

    def test_target_rename(self):
        args = ["entry1"]
        molot.core._args = args

        @target(name="entry2")
        def entry1():
            logging.debug("entry")

        self.assertIn("entry2", molot.core._state.targets)
        molot.core._state.targets_to_execute(["entry2"])  # test contents

        self.assertNotIn("entry1", molot.core._state.targets)
        self.assertRaises(
            TargetNotFoundError,
            lambda: molot.core._state.targets_to_execute(args),
        )

        self.assertRaises(MockSys.ExitError, evaluate)
