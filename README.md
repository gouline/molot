# Molot

[![GitHub Actions](https://github.com/gouline/molot/actions/workflows/master.yml/badge.svg)](https://github.com/gouline/molot/actions/workflows/master.yml)
[![PyPI](https://img.shields.io/pypi/v/molot)](https://pypi.org/project/molot/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/gouline/molot/blob/master/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

Simple execution orchestrator.

## Requirements

Molot requires Python 3.8 or above.

For development, you will need [uv](https://docs.astral.sh/uv/getting-started/installation/) installed.

## Usage

Create a new orchestration file, e.g. `build.py` for a build orchestration. Make it executable `chmod +x build.py` to make it easier to run.

```py
#!/usr/bin/env python3
from molot import *  # pylint: disable=wildcard-import,unused-wildcard-import

# Your targets and environment arguments here

evaluate()
```

Pylint comment silences editor warnings about wildcard imports, you can alternatively import everything individually.

Now you're ready to run the build script to see the help message:

```shell
./build.py
```

To only see a list of targets and environment arguments, call the built-in `list` target:

```shell
./build.py list
```

Not very exciting so far, let's learn how to add your own targets and environment arguments.

### Targets

Any piece of work that your build needs to perform is defined as a target. Here's a trivial example of a target that executes `ls`.

```py
@target(
    name="ls",
    description="lists current directory items",
    group="greetings",
    depends=["target1", "target2"]
)
def ls():
    shell("ls")
```

Parameters explained:

* `name` - unique name to reference the target (optional; function name is used by default)
* `description` - short description of what the target does displayed in the help message (optional)
* `group` - grouping to list target under (optional; listed under "ungrouped" by default)
* `depends` - list of other targets that must be executed first (optional)

Since all the parameters are optional, the shortest definition of the same target can be as follows:

```py
@target()
def ls():
    shell("ls")
```

Here's how you run your new target:

```shell
./build.py ls
```

#### Dependency Resolution

Now we can define another target `hello` that depends on `ls`:

```py
@target(description="say hello", depends=["ls"])
def hello():
    print("hello")
```

There is basic dependency resolution that checks for circular dependencies and finds all transitive dependency targets to execute before running the one that you called. When you call:

```shell
./build.py hello
```

What actually happens is equivalent to calling:

```shell
./build.py ls hello
```

### Environment Arguments

Environment arguments ar a cross between environment variables and arguments. Values can be passed as the former and then overriden as the latter.

Here's how you define one:

```py
ENV = envarg("ENV", default="dev", description="build environment")
```

Parameters explained:

* `name` - unique name for the argument
* `default` - default value if none is supplied (optional; `None` by default)
* `description` - short description of what the argument is displayed in the help message (optional)
* `sensitive` - indicates the value is sensitive and should be masked (optional)

The argument is evaluated right there (not inside of targets), so you can use that variable straightaway.

It can be set as a regular environment variable:

```shell
ENV=dev ./build.py sometarget
```

Alternatively, it can be passed as an argument:

```shell
./build.py sometarget --arg ENV=prod
```

Finally, you can pass .env file to load:

```shell
./build.py sometarget --dotenv /path/to/.env
```

If both are passed simultaneously, then argument takes precedence over the environment variable.

## Examples

See [examples](./examples) for use cases that demonstrate the main features.
