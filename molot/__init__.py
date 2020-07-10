"""
Base script execution functionality (can be imported separately).
"""

__version__ = '0.6.0'

import sys
import os
import logging
import argparse
import collections
import subprocess
import types
import io
import shutil
import importlib.util
from typing import Any

# Logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

class ShutdownHandler(logging.Handler):
    def emit(self, record):
        logging.shutdown()
        sys.exit(1)

logging.getLogger().addHandler(ShutdownHandler(level=50))

# Path to project root (usable in script)
PROJECT_PATH = os.path.dirname(sys.argv[0])

# Holder for internal script state
class _State:
    def __init__(self):
        self.targets = dict()
        self.envargs = dict()
        self.envarg_vals_base = dict()
        self.envarg_vals_override = dict()
        self._preparse_envargs()

        self.config_path = None
        self.config = None
        self.envconfig = None
        
    def _preparse_envargs(self):
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--arg', nargs='*')
        args, _ = parser.parse_known_args()

        if args.arg:
            for a in args.arg:
                aparts = a.split('=', 1)
                if len(aparts) >= 2:
                    self.envarg_vals_override[aparts[0]] = aparts[1]

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
    # P1: override passed via --arg
    if name in _STATE.envarg_vals_override:
        return _STATE.envarg_vals_override[name]
    
    # P2: environment variable
    val = os.getenv(name)
    if val is not None:
        return val
    
    # P3: properties file passed via envargs_file()
    if name in _STATE.envarg_vals_base:
        return _STATE.envarg_vals_base[name]
    
    # P4: provided default
    return default

def _read_properties(path: str, sep='=', comment_char='#') -> dict:
    """Read the file passed as parameter as a properties file.
    
    Source: https://stackoverflow.com/a/31852401/818393
    
    Arguments:
        path {str} -- Path to properties file.
    
    Keyword Arguments:
        sep {str} -- Key-value separator. (default: {'='})
        comment_char {str} -- Character denoting comment lines. (default: {'#'})
    
    Returns:
        dict -- Dictionary of properties.
    """

    props = {}
    with open(path, "rt") as f:
        for line in f:
            l = line.strip()
            if l and not l.startswith(comment_char):
                key_value = l.split(sep)
                key = key_value[0].strip()
                value = sep.join(key_value[1:]).strip().strip('"') 
                props[key] = value
    return props

def envarg(name: str, default: str = None, description: str = "") -> str:
    """Decorator for string environment argument.
    
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

def envarg_bool(name: str, default: bool = False, description: str = "") -> bool:
    """Decorator for boolean environment argument.
    
    Arguments:
        name {str} -- Unique name.
    
    Keyword Arguments:
        default {str} -- Default value. (default: {False})
        description {str} -- Human-readable description. (default: {""})
    
    Returns:
        bool -- Retrieved or default value.
    """

    v = envarg(name, str(default), description)
    if v:
        return v.lower() == 'true'
    return False

def envarg_int(name: str, default: int = 0, description: str = "") -> int:
    """Decorator for integer environment argument.
    
    Arguments:
        name {str} -- Unique name.
    
    Keyword Arguments:
        default {int} -- Default value. (default: {0})
        description {str} -- Human-readable description. (default: {""})
    
    Returns:
        int -- Retrieved or default value.
    """

    v = envarg(name, str(default), description)
    try:
        return int(v)
    except ValueError:
        return default

def envargs_file(path: str):
    """Reads environment arguments from file and save them as defaults.

    This expects a simple properties file of form:
        # Some comment
        KEY1 = VALUE1
        KEY2=VALUE2
        KEY3 = "VALUE3"
    
    Arguments:
        path {str} -- Path to configuration file.
    """

    if os.path.isfile(path):
        props = _read_properties(path)
        for k, v in props.items():
            if k not in _STATE.envarg_vals_base:
                _STATE.envarg_vals_base[k] = v
    else:
        print("Envargs {} not found".format(path))

#endregion

#region Script functions

def evaluate():
    """Evaluates your scripts. Call to evaluate() must be at the very end of your script!
    """

    print("→ Running Molot {}...".format(__version__))

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_list_targets_str()
    )
    parser.add_argument('targets', metavar='TARGET', type=str, nargs='*',
                    help="target to execute", default=['list'])
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

def build():
    """Alias for evaluate() for backwards compatibility.
    """

    evaluate()

class ReturnCodeError(Exception):
    """Error for failed shell commands in piped mode.
    """

    def __init__(self, code: int, output: str):
        """Constructor.
        
        Arguments:
            code {int} -- Return code from shell.
            output {str} -- Text output of error.
        """

        self.code = code
        self.output = output

def shell(command: str, piped: bool = False) -> str:
    """Runs shell command.
    
    Arguments:
        command {str} -- Raw command to run in your shell.
    
    Keyword Arguments:
        piped {bool} -- Returns output as string if true, otherwise prints it in stdout. (default: {False})
    
    Returns:
        str -- Returns string output when piped, nothing otherwise.
    """

    pipe = None
    if piped:
        pipe = subprocess.PIPE
    
    # Allow arbitrary indentation of block strings
    command = '\n'.join([x.lstrip() for x in command.split('\n')])

    print("+ Shell: {}".format(command))

    p = subprocess.Popen(command, shell=True, stdout=pipe, stderr=pipe)
    out, err = p.communicate()

    if p.returncode != 0:
        if piped:
            raise ReturnCodeError(p.returncode, err.decode('utf-8'))
        else:
            sys.exit(p.returncode)

    if piped: 
        return out.decode('utf-8')
    return None

#endregion
