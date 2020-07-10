"""
Functionality specific to build scripts.
"""

from . import * #pylint: disable=unused-wildcard-import

import ruamel.yaml as yaml
from munch import munchify

# Holder for internal builder state
class _BuildState:
    def __init__(self):
        self.config_path = None
        self.config = None
        self.envconfig = None

_BUILD_STATE = _BuildState()

ENV = envarg('ENV', description="build environment, e.g. dev, test, prod")

#region Build script functions

def load_config(path: str) -> Any:
    """Loads configuration from path.
    
    Arguments:
        path {str} -- Path to configuration file.
    
    Returns:
        Any -- Configuration dictionary or list (supports munch attribute notation).
    """

    config = dict()
    if os.path.isfile(path):
        with open(path, 'r') as stream:
            try:
                config = yaml.round_trip_load(stream, preserve_quotes=True)
                config = munchify(config)
            except yaml.scanner.ScannerError as exc:
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
        Any -- Loaded configuration dict, list (support munch attribute notation) or None.
    """

    config = None
    if _BUILD_STATE.config:
        if _BUILD_STATE.config_path != path:
            logging.critical("Attempting to reload configuration")
        else:
            config = _BUILD_STATE.config
    else:
        config = load_config(path)
        _BUILD_STATE.config = config
        _BUILD_STATE.config_path = path

    if len(keys) > 0:
        config = getpath(config, keys)
        if required and config == None:
            safe_keys = map(lambda x: x if x != None else 'None', keys)
            logging.critical("Cannot find %s in configuration", '->'.join(safe_keys))

    if isinstance(config, dict) or isinstance(config, list):
        return config.copy()
    return config

def envconfig(keys = [], root = 'Environments', inherit = 'Inherit') -> dict:
    """Loads environment-specific configuration or returns previously loaded one.

    Environment-specific configuration is part of regular configuration, it's just
    a dictionary indexed by the ENV environment argument that contains values specific
    to current running environment.

    It also allows keys to be inherited by the environment name.
    
    Keyword Arguments:
        keys {list} -- List of recursive keys to retrieve. (default: {[]})
        root {str} -- Name of root element containing environment-specific configuration. (default: {'Environments'})
        inherit {str} -- Name of parameter containing environment to inherit from. (default: {'Inherit'})
    
    Returns:
        dict -- Loaded configuration dictionary (supports munch attribute notation).
    """

    envconfig = None
    if _BUILD_STATE.envconfig:
        envconfig = _BUILD_STATE.envconfig
    else:
        envconfig = config([root, ENV])
        while inherit in envconfig:
            fields = config([root, envconfig.pop(inherit)])
            fields = {k: v for k, v in fields.items() if k not in envconfig}
            envconfig.update(fields)
        _BUILD_STATE.envconfig = envconfig
    
    return getpath(envconfig, keys)

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

def flatten(x: dict, prefix = '', grouped = True) -> dict:
    """Flattens dictionary by a group (one level only).
    
    Arguments:
        x {dict} -- Dictionary to be flattened.
    
    Keyword Arguments:
        prefix {str} -- Group prefix to flatten by. (default: {''})
        grouped (bool) -- True if parameters are internally grouped by key. (default: {True})
    
    Returns:
        dict -- New flattened dictionary.
    """

    output = {}

    def flatten_inner(x: dict, output: dict, prefix: str):
        for k, v in x.items():
            output[f"{prefix}{k}"] = v

    if grouped:
        for k, v in x.items():
            flatten_inner(v, output, prefix + k)
    else:
        flatten_inner(x, output, prefix)
    return output

def git_hash() -> str:
    """Extracts Git hash from current directory.
    
    Returns:
        str -- Git hash encoded as UTF-8.
    """

    return subprocess.Popen(['git', 'rev-parse', '--verify', 'HEAD'], stdout=subprocess.PIPE) \
        .communicate()[0] \
        .decode('utf-8') \
        .replace('\n', '')


def md5(*files: list) -> str:
    """Computes MD5 checksum of files.
    
    Returns:
        str -- Combined MD5 checksum for multiple files.
    """

    import hashlib
    hash = hashlib.md5()
    for f in files:
        if os.path.isfile(f):
            hash.update(open(f, 'rb').read())
    return hash.hexdigest()

#endregion
