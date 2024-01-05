# pylint: disable=protected-access
import unittest

import molot
from molot import (
    CIRCULAR_DEPENDENCY,
    SUCCESS,
    envarg,
    envarg_bool,
    envarg_int,
    evaluate,
    target,
)
from molot.state import State


class TestEvaluate(unittest.TestCase):
    def setUp(self):
        molot._state = State()

    def test_circular(self):
        @target(depends=["dep2"])
        def dep1():
            print("dep1")

        @target(depends=["dep1"])
        def dep2():
            print("dep2")

        @target(depends=["dep1", "dep2"])
        def tests():
            print("tests")

        self.assertEqual(CIRCULAR_DEPENDENCY, evaluate(_suppress_exit=True))

    def test_happy(self):
        self.assertEqual("", envarg("ARG_STR", default=""))
        self.assertEqual(42, envarg_int("ARG_INT", default=42))
        self.assertEqual(True, envarg_bool("ARG_BOOL", default=True))

        @target()
        def dep3():
            print("dep3")

        @target(depends=["dep3"])
        def dep4():
            print("dep4")

        @target(depends=["dep3", "dep4"])
        def tests():
            print("tests")

        self.assertEqual(SUCCESS, evaluate(_suppress_exit=True))
