# pylint: disable=protected-access
import logging
import unittest

import molot.core
from molot import ResultCode, envarg, envarg_bool, envarg_int, evaluate, reset, target


class TestCore(unittest.TestCase):
    def test_circular(self):
        molot.core._args = ["entry"]
        reset()

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
        self.assertEqual(ResultCode.CIRCULAR_DEPENDENCY, evaluate(exit_on_error=False))

    def test_happy(self):
        molot.core._args = ["entry"]
        self.assertIn("list", molot.core._state.targets)
        reset()
        self.assertIn("list", molot.core._state.targets)

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

        @target(depends=["dep3", "dep4"])
        def entry():
            logging.debug("entry")

        self.assertIn("dep3", molot.core._state.targets)
        self.assertIn("dep4", molot.core._state.targets)
        self.assertIn("entry", molot.core._state.targets)
        self.assertEqual(ResultCode.SUCCESS, evaluate(exit_on_error=False))

    def test_rename_target(self):
        reset()

        @target(name="entry2")
        def entry1():
            logging.debug("entry")

        self.assertIn("entry2", molot.core._state.targets)
        molot.core._args = ["entry2"]
        self.assertEqual(ResultCode.SUCCESS, evaluate(exit_on_error=False))

        self.assertNotIn("entry1", molot.core._state.targets)
        molot.core._args = ["entry1"]
        self.assertEqual(ResultCode.TARGET_NOT_FOUND, evaluate(exit_on_error=False))
