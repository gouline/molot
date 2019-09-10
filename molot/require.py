import os
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
            raise ValueError("Unrecognized type {}".format(p))

        try:
            spec = importlib.util.find_spec(module)
        except ModuleNotFoundError:
            spec = None
        
        if not spec:
            pip = os.getenv('PIP', 'pip3')
            subprocess.run([pip, 'install', '--upgrade', package])
