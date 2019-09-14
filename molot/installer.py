import subprocess
import logging
import importlib.util
from molot import envarg

_INSTALLER = envarg('INSTALLER', default='pip3 install', description="command to install external packages")

def install(packages: list):
    """Installs external packages.
    
    Arguments:
        packages {list} -- List of external packages, if package and module 
            name are the same; otherwise list of tuples (module, package).
    """

    for p in packages:
        if type(p) is tuple:
            module, package = p
        elif type(p) is str:
            module, package = (p, p)
        else:
            raise ValueError("Unrecognized type {}".format(p))

        try:
            spec = importlib.util.find_spec(module)
        except ModuleNotFoundError:
            spec = None
        
        if not spec:
            cmd = [*_INSTALLER.split(), package]
            print("→ Installing: {}".format(' '.join(cmd)))
            proc = subprocess.run(cmd)
            if proc.returncode != 0:
                logging.critical("Installer failed (code %d)", proc.returncode)
