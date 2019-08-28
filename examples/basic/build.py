#!/usr/bin/env python

from molot import * #pylint: disable=unused-wildcard-import

ENV = envarg('ENV', default='dev', description="build environment")

@target(description="lists current directory items")
def ls():
    shell("ls")

@target(description="says a friendly hello", group='greetings')
def hello():
    print(f"hello, {config(['Environments', ENV, 'Name'], required=True)}!")

@target(description="says goodbye", group='greetings', depends=['hello'])
def goodbye():
    print("goodbye!")

build()
