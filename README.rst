Molot
#####

Lightweight build tool for software projects.

Requirements
============

Molot requires Python 3.6 or above (3.5 should work too, but that's untested).

Usage
=====

To create a build script, just make a new file ``build.py`` in the root of your
project. You can make it executable ``chmod +x build.py`` to make it easier to
run it.

Here's how to start your build script.

.. code-block:: python

    #!/usr/bin/env python3
    from molot import * #pylint: disable=unused-wildcard-import

Note that ``#pylint: disable=unused-wildcard-import`` is optional but will help
keep your editor quiet about unused imports.

Once you've defined your targets and all, do this at the end to compile them:

.. code-block:: python

    build()

Now you're ready to run the build script to see the help message:

.. code-block:: bash

    ./build.py

If you only wanted to see the list of targets and environment arguments, you
run the built-in target ``list`` as follows:

.. code-block:: bash

    ./build.py list

The output will be something like this:

.. code-block::

    → Executing target: list
    available targets:
    <builtin>
        list - lists all available targets

    environment arguments:

Not very exciting. Now let's learn how to add targets and environment
arguments.

Targets
-------

Any piece of work that your build script needs to perform is defined as a
target. Here's a trivial example of a target that just runs ``ls``.

.. code-block:: python

    @target(
        name='ls',
        description="lists current directory items",
        group='greetings',
        depends=['target1', 'target2']
    )
    def ls():
        shell("ls")

Parameters are as follows:

* ``name`` - unique name to use when requesting the target (optional; by
  default the function name will be used)
* ``description`` - short description about what the target does, to be
  displayed in the help message (optional)
* ``group`` - group name to list target under alphabetically (optional;
  by default, will be listed under ungrouped)
* ``depends`` - list of other targets that need to be executed first
  (optional)

Since all the parameters are optional, the shortest definition of the same
target can be as follows:

.. code-block:: python

    @target()
    def ls():
        shell("ls")

There is a basic dependency resolution routine that checks for circular
dependencies and finds the first targets to execute before running the one that
you requested.

Anyway, here's how you run your new target:

.. code-block:: bash

    ./build.py ls

Environment Arguments
---------------------

Environment arguments are intended as a cross between environment variables and
arguments. Values can be passed as the former and then overriden as the latter.

Here's how you define one:

.. code-block:: python

    ENV = envarg('ENV', default='dev', description="build environment")

Parameters are as follows:

* ``name`` - unique name for the argument
* ``default`` - default value if none is supplied (optional; by default
  ``None``)
* ``description`` - short description about what the argument is, to be
  displayed in the help message (optional)

The argument is evaluated right there (rather than inside of targets), so you
can use that variable anywhere once it's set.

It can either be set as a regular environment variable. For example:

.. code-block:: bash

    ENV=dev ./build.py sometarget

Alternatively, it can be passed as an argument:

.. code-block:: bash

    ./build.py sometarget --arg ENV=prod

If both are passed simultaneously (not recommended), then argument takes
precedence over the environment variable.

Configuration
-------------

Molot provides an optional configuration parsing facility.

If you want to specify a configuration YAML file, create a file ``build.yaml``
in your project root, same location as your ``build.py``, and fill it with any
valid YAML. For example, something like this:

.. code-block:: yaml

    Environments:
        dev:
            Name: development
        prod:
            Name: production

Now you can access these configurations by calling ``config()`` from anywhere.
First call will do the initial parsing, subsequent ones will just returned a
cached dictionary with your configurations.

Therefore, if you want to parse a YAML file with a different name, pass the
path to the first call:

.. code-block:: python

    config(path=os.path.join(PROJECT_PATH, 'somethingelse.yaml'))

You can either get the whole configuration dictionary or pass a specific path
of keys to extract. For example, if you want to get the name for the ``prod``
environment:

.. code-block:: python

    name = config(['Environments', 'prod', 'Name'])

If the desired key is optional and you don't want to fail the execution if it's
not there, you can do the following:

.. code-block:: python

    name = config(['Environments', 'qa', 'Name'], required=False)

Bootstrap
---------

The build script above assumes Molot is already installed. If not, there are
some tricks that you can use to pre-install before the script runs.

For example, you can create a separate file ``build_boot.py`` as follows:

.. code-block:: python

    from subprocess import run
    from importlib.util import find_spec as spec
    from pkg_resources import get_distribution as dist

    # Preloads Molot build tool.
    def preload_molot(ver):
        mod, pkg = 'molot', 'molot'
        spec(mod) and dist(pkg).version == ver or run(['pip3', 'install', f"{pkg}=={ver}"])

Then at the top of your script, you'll be able to do the following:

.. code-block:: python

    #!/usr/bin/env python3
    __import__('build_boot').preload_molot('X.Y.Z')
    from molot import * #pylint: disable=unused-wildcard-import

This downloads a specific version ``X.Y.Z`` if it's not already installed.

Installer
---------

There is an installer for external packages that you can use to install
dependencies only when they're needed.

.. code-block:: python

    from molot.installer import install
    install([
        'package1',
        ('module2', 'package2>=1.2.3')
    ])

Notice that you can pass a list of packages to install in two formats:

* When the module name (``import`` statement) matches the install package name,
  you can just pass it as a string, i.e. like ``'package1'`` in the example
* When they differ or you want to provide a specific version of a package,
  pass a tuple with the module name first and the install statement second,
  i.e. like ``('module2', 'package2>=1.2.3')`` in the example

The ``install()`` expression checks if the module can be imported (meaning that
it's already installed) and installs it otherwise.

By default, the installer uses ``pip3 install`` but if you want to use a
different expression (e.g. different version of ``pip`` or ``conda``), you can
pass it using the ``INSTALLER`` environment argument.

.. code-block:: bash

    INSTALLER="conda install" ./build.py

Contexts
--------

Although you can do all the work within each target, you can also abstract it
into "contexts". While you can use this concept however you like, the intended
use was creating an object that extends ``Context`` that sets up the arguments,
paths and anything else your target needs, and then calling a method on it.

Here's an example:

.. code-block:: python

    PATH = './'
    ENV = 'dev'

    @target()
    def create_foo():
        FooContext(PATH, ENV).create()

    @target()
    def delete_foo():
        FooContext(PATH, ENV).delete()

    from molot.context import Context

    class FooContext(Context):

        def __init__(self, path, env):
            self.path = path
            self.env = env

        def create(self):
            self.ensure_dir(self.path)
            # Do something with self.env

        def delete(self):
            self.ensure_dir(self.path)
            # Do something with self.env

It might be a good idea to then extract your contexts into a separate file
``build_contexts.py`` and import them in your ``build.py``. That way, your
build script is nice and clean with only the targets, meanwhile all your
under-the-hood implementation is hidden away in a separate file.

Examples
========

See examples directory for sample build scripts that demonstrate some features.
