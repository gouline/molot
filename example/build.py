#!/usr/bin/env python

# Remove/comment next line to work with pip package
from os import path, sys

sys.path.insert(0, path.join(path.dirname(sys.argv[0]), "..", ".."))

from molot import *  # pylint: disable=wildcard-import,unused-wildcard-import

envargs_file("config.env")

HOST = envarg("HOST", default="localhost", description="API host")
PORT = envarg_int("PORT", default=80, description="API port number")
TOKEN = envarg("TOKEN", description="API token", sensitive=True)
HTTPS = envarg_bool("HTTPS", default=True, description="use HTTPS to connect")


@target(description="says a friendly hello", group="api")
def validate():
    assert len(TOKEN) == 16, "token must be 16 characters long"


@target(description="says goodbye", group="api", depends=["validate"])
def connect():
    print(f"connecting to {'https' if HTTPS else 'http'}://{HOST}:{PORT}")


evaluate()
