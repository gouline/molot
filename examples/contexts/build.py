#!/usr/bin/env python
from molotcontexts import install_molot
install_molot('0.2.2')

from molot import * #pylint: disable=unused-wildcard-import

@target(description="lists current directory items")
def ls():
    shell("ls")

build()
