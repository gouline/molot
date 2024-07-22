from molot import shell


def test_shell_ls():
    assert shell("ls -1 LICENSE", piped=True) == "LICENSE\n"
