# pylint: disable=protected-access
import logging
import unittest
from pathlib import Path

import molot.core
from molot import envarg, envarg_bool, envarg_int, envargs_file, reset, target
from molot.state import TargetCircularDependencyError, TargetNotFoundError


class TestCore(unittest.TestCase):
    def setUp(self):
        self.assertIn("list", molot.core._state.targets)
        reset()
        self.assertIn("list", molot.core._state.targets)

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

    def test_circular(self):
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
            lambda: molot.core._state.targets_to_execute(["entry"]),
        )

    def test_happy(self):
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
        targets = molot.core._state.targets_to_execute(["entry"])
        target_names = [t.name for t in targets]  # deque is reversed
        self.assertEqual(["entry", "dep4", "dep3"], target_names)

        targets = molot.core._state.targets_by_group()
        self.assertEqual(["<builtin>", "<ungrouped>", "group1"], list(targets.keys()))
        self.assertEqual(["list"], [t.name for t in targets["<builtin>"]])
        self.assertEqual(["dep3", "dep4"], [t.name for t in targets["<ungrouped>"]])
        self.assertEqual(["entry"], [t.name for t in targets["group1"]])

    def test_rename_target(self):
        @target(name="entry2")
        def entry1():
            logging.debug("entry")

        self.assertIn("entry2", molot.core._state.targets)
        molot.core._state.targets_to_execute(["entry2"])  # test contents

        self.assertNotIn("entry1", molot.core._state.targets)
        self.assertRaises(
            TargetNotFoundError,
            lambda: molot.core._state.targets_to_execute(["entry1"]),
        )
