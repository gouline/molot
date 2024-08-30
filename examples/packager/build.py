#!/usr/bin/env python3
from molot import *

CREATE_DIST = envarg_bool(
    "CREATE_DIST",
    description="create dist/ directory if it doesn't exist",
    default=True,
)


@target(description="create necessary directories")
def prepare():
    if CREATE_DIST:
        shell("mkdir -p dist")


@target(description="package function as a ZIP file", depends=["prepare"])
def package():
    shell("zip dist/package.zip function.py config.json")


evaluate()
