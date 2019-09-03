import subprocess
import importlib.util
import logging

def install(packages: list):
    """Installs pip packages.
    
    Arguments:
        packages {list} -- List of pip packages, if package and module name are 
            the same; otherwise list of tuples (module, package).
    """
    
    for p in packages:
        if type(p) is tuple:
            module, package = p
        elif type(p) is str:
            module, package = (p, p)
        else:
            logging.fatal("Unrecognized type %s", p)
        if not importlib.util.find_spec(module):
            subprocess.run(['pip3', 'install', '--upgrade', package])
