#!/usr/bin/env python

from molot import *  # pylint: disable=unused-wildcard-import


@target(description="lists current directory items")
def ls():
    shell("ls")


build()
