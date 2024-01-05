import unittest

from molot import shell


class TestHelpers(unittest.TestCase):
    def test_ls(self):
        self.assertEqual("LICENSE\n", shell("ls -1 LICENSE", piped=True))
