#!/usr/bin/env python

# Remove/comment next line to work with pip package
from os import path, sys

sys.path.insert(0, path.join(path.dirname(sys.argv[0]), "..", ".."))

from molot.builder import *  # pylint: disable=unused-wildcard-import

envargs_file(os.path.join(PROJECT_PATH, "credentials.env"))

API_TOKEN = envarg("API_TOKEN")


@target(description="lists current directory items")
def ls():
    shell("ls")


@target(description="says a friendly hello", group="greetings")
def hello():
    print(f"hello, {config(['Environments', ENV, 'Name'], required=True)}!")


@target(description="says a friendly hello (uses envconfig call)", group="greetings")
def hello_envconfig():
    print(f"hello, {config(['Environments', ENV, 'Name'], required=True)}!")


@target(
    description="says a friendly hello (uses munch attribute notation)",
    group="greetings",
)
def hello_munch():
    print(f"hello, {envconfig().Name}!")


@target(description="says goodbye", group="greetings", depends=["hello"])
def goodbye():
    print("goodbye!")


build()
