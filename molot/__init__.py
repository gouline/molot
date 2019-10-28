
import sys
import os
import shutil
import logging
import argparse
import collections
import subprocess
import types
import io
import yaml
import importlib.util
from typing import Any

__version__ = '0.2.4'

# Import message
print("→ Running Molot {} build...".format(__version__))

# Logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

class ShutdownHandler(logging.Handler):
    def emit(self, record):
        logging.shutdown()
        sys.exit(1)

logging.getLogger().addHandler(ShutdownHandler(level=50))

# Path to project root (usable in build.py)
PROJECT_PATH = os.path.dirname(sys.argv[0])

# Holder for internal builder state
class _State:
    def __init__(self):
        self.targets = dict()
        self.envargs = dict()
        self.envargvals = dict()
        self._preparse_envargs()

        self.config_path = None
        self.config = None
        
    def _preparse_envargs(self):
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--arg', nargs='*')
        args, _ = parser.parse_known_args()

        if args.arg:
            for a in args.arg:
                aparts = a.split('=', 1)
                if len(aparts) >= 2:
                    self.envargvals[aparts[0]] = aparts[1]

_STATE = _State()

#region Targets

class _TargetDef:
    def __init__(self, name: str, description: str, group: str, phony: bool, depends: list, f):
        self.name = name
        self.description = description
        self.group = group
        self.depends = depends
        self.phony = phony
        self.f = f

def target(name: str = "", description: str = "", group: str = "<ungrouped>", depends: list = [], phony: bool = False) -> types.FunctionType:
    """Decorator for executable targets.
    
    Keyword Arguments:
        name {str} -- Unique name. (default: {""})
        description {str} -- Human-readable description. (default: {""})
        group {str} -- Name for grouping when being listed. (default: {""})
        depends {list} -- List of targets it depends on. (default: {[]})
        phony {bool} -- Determines whether target is a phony and doesn't use environment. (default: {False})
    
    Returns:
        types.FunctionType -- Decorator function.
    """
    
    def decorator(f):
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        
        tname = name if len(name) > 0 else f.__name__
        _STATE.targets[tname] = _TargetDef(
            name=tname,
            description=description if description else "<no description>",
            group=group,
            depends=depends,
            phony=phony,
            f=f
        )
        return wrapper
    return decorator

def _list_targets_str() -> str:
    out = io.StringIO()

    targets = list(_STATE.targets.values())
    if len(targets) > 0:
        print("available targets:", file=out)
        targets.sort(key=lambda x: (x.group.lower(), x.name.lower()))
        targets_group = None
        for target in targets:
            depends = "(depends: {})".format(', '.join(target.depends)) if target.depends else ''
            if targets_group != target.group:
                targets_group = target.group
                print("  {}".format(target.group), file=out)
            print("    {} - {} {}".format(target.name, target.description, depends), file=out)

    if len(_STATE.envargs) > 0:
        print("\nenvironment arguments:", file=out)
        for aname in _STATE.envargs:
            arg = _STATE.envargs[aname]
            print("  {} - {} (default: {})".format(arg.name, arg.description, arg.default), file=out)
    
    return out.getvalue()

@target(name='list', description="lists all available targets", group="<builtin>", phony=True)
def _list_targets():
    print(_list_targets_str(), end='')

#endregion

#region Environment arguments

class _EnvArgDef:
    def __init__(self, name: str, description: str, default: str):
        self.name = name
        self.description = description
        self.default = default

def _envargval(name: str, default: str) -> str:
    if name in _STATE.envargvals:
        return _STATE.envargvals[name]
    return os.getenv(name, default)

def envarg(name: str, default: str = None, description: str = "") -> str:
    """Decorator for environment argument.
    
    Arguments:
        name {str} -- Unique name.
    
    Keyword Arguments:
        default {str} -- Default value. (default: {None})
        description {str} -- Human-readable description. (default: {""})
    
    Returns:
        str -- Retrieved or default value.
    """

    _STATE.envargs[name] = _EnvArgDef(
        name=name,
        description=description if description else "<no description>",
        default=default
    )
    return _envargval(name, default)

#endregion

#region Build script functions

def load_config(path: str) -> Any:
    """Loads configuration from path.
    
    Arguments:
        path {str} -- Path to configuration file.
    
    Returns:
        Any -- Configuration dictionary or list.
    """

    config = dict()
    if os.path.isfile(path):
        with open(path, 'r') as stream:
            try:
                config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print("Cannot parse config {}: {}".format(path, exc))
    else:
        print("Config {} not found".format(path))
    return config

def config(keys: list = [], required: bool = True, path: str = os.path.join(PROJECT_PATH, 'build.yaml')) -> Any:
    """Loads configuration from file or returns previously loaded one.

    Loading from file will be done on the first call. Subsequent loads from different file
    will raise a fatal error. If you have multiple configuration files, use load_config()
    directly and store those multiple configurations in build.py.
    
    Arguments:
        keys {list} -- List of recursive keys to retrieve.

    Keyword Arguments:
        required {bool} -- Throws fatal error if not found, when set to True (default: {True})
        path {str} -- Path to configuration file. (default: {PROJECT_PATH/build.yaml})
    
    Returns:
        Any -- Loaded configuration dict, list or None.
    """

    config = None
    if _STATE.config:
        if _STATE.config_path != path:
            logging.critical("Attempting to reload configuration")
        else:
            config = _STATE.config
    else:
        config = load_config(path)
        _STATE.config = config
        _STATE.config_path = path

    if len(keys) > 0:
        config = getpath(config, keys)
        if required and config == None:
            safe_keys = map(lambda x: x if x != None else 'None', keys)
            logging.critical("Cannot find %s in configuration", '->'.join(safe_keys))

    return config

def build():
    """Executes build. Call to build() must be at the end of build.py!
    """

    parser = argparse.ArgumentParser(
        description='Project build script.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_list_targets_str()
    )
    parser.add_argument('targets', metavar='TARGET', type=str, nargs='*',
                    help="build target to execute", default=['list'])
    parser.add_argument('--arg', metavar='KEY=VALUE', nargs='*',
                    help="overwrite environment arguments")
    args = parser.parse_args()

    to_evaluate = collections.deque()
    to_evaluate.extendleft(args.targets)
    evaluated = {}
    to_execute = collections.deque()
    while len(to_evaluate) > 0:
        name = to_evaluate[-1]
        if name not in _STATE.targets:
            print("Target not found:", name, "\n")
            _list_targets()
            break

        target = _STATE.targets[name]
        logging.debug("Evaluating target %s", name)
        
        deps_satisfied = True
        for dname in reversed(target.depends):
            if dname not in evaluated or not evaluated[dname]:
                to_evaluate.append(dname)
                deps_satisfied = False

        if not deps_satisfied:
            if name in evaluated:
                print("Circular dependency detected when evaluating target {}".format(name))
                return
            else:
                evaluated[name] = False
                continue
        
        if name not in evaluated or not evaluated[name]:
            to_execute.appendleft(target)
        
        evaluated[name] = True
        to_evaluate.pop()

    env_listed = False
    while len(to_execute) > 0:
        target = to_execute.pop()

        if not env_listed and not target.phony:
            print("environment:")
            for key, var in _STATE.envargs.items():
                print("  {}={}".format(key, _envargval(key, var.default)))
            print()
            env_listed = True

        print("→ Executing target:", target.name)
        target.f()

def shell(command: str, piped: bool = False, silent: bool = False) -> str:
    """Runs shell command.
    
    Arguments:
        command {str} -- Raw command to run in your shell.
    
    Keyword Arguments:
        piped {bool} -- Returns output as string if true, otherwise prints it in stdout. (default: {False})
        silent {bool} -- Suppresses printing of command before running it. (default: {False})
    
    Returns:
        str -- Returns string output when piped, nothing otherwise.
    """

    stdout = None
    if piped:
        stdout=subprocess.PIPE

    if not silent:
        print("+ {}".format(command))

    p = subprocess.Popen(command, shell=True, stdout=stdout)
    pcomm = p.communicate()
    if piped: 
        return pcomm[0].decode("utf-8")
    
    return None

def getpath(x: Any, keys: list) -> Any:
    """Gets recursive key path from dictionary or list.
    
    Arguments:
        x {Any} -- Dictionary or list.
        keys {list} -- List of recursive keys to retrieve.
    
    Returns:
        Any -- Retrieved dictionary, list or None.
    """

    for key in keys:
        if isinstance(x, dict):
            if key not in x:
                return None
        elif isinstance(x, list):
            if not isinstance(key, int):
                return None
        else:
            return None
        x = x[key]
    return x

#endregion
