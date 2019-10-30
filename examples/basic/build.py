#!/usr/bin/env python

# Remove/comment next line to work with pip package
from os import path, sys; sys.path.insert(0, path.join(path.dirname(sys.argv[0]), '..', '..')) 

from molot import * #pylint: disable=unused-wildcard-import

print(envconfig())

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
