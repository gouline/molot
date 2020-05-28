#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [[ ! -d "$DIR/.venv" ]]; then
    echo "Creating new venv..."
    python3 -m venv .venv \
        && source .venv/bin/activate \
        && pip3 install --upgrade pip \
        && pip3 install "molot>=0.5.1,<0.6.0"
else
    source .venv/bin/activate
fi

$DIR/build.py $@