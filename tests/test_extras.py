import unittest

from molot import shell


class TestExtras(unittest.TestCase):
    def test_shell_ls(self):
        self.assertEqual("LICENSE\n", shell("ls -1 LICENSE", piped=True))
