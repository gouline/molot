#!/usr/bin/env python3
import json
from pathlib import Path

import requests

from molot import envarg, envarg_int, evaluate, target

GITHUB_TOKEN = envarg(
    "GITHUB_TOKEN",
    description="GitHub API token for private releases",
    sensitive=True,
)
MAX_RESULTS = envarg_int(
    "MAX_RESULTS",
    default=100,
    description="maximum releases to load from API",
)

RELEASES_PATH = Path("downloads") / "releases.json"


@target(description="fetch GitHub releases")
def fetch():
    headers = {"X-GitHub-Api-Version": "2022-11-28"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    resp = requests.get(
        "https://api.github.com/repos/gouline/molot/releases",
        params={"per_page": MAX_RESULTS},
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()

    RELEASES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RELEASES_PATH, "wb") as f:
        f.write(resp.content)


@target(description="print latest release", depends=["fetch"])
def latest():
    with open(RELEASES_PATH, "rb") as f:
        print("Latest release", json.load(f)[0].get("name"))


@target(description="print oldest release", depends=["fetch"])
def oldest():
    with open(RELEASES_PATH, "rb") as f:
        print("Oldest release", json.load(f)[-1].get("name"))


evaluate()
