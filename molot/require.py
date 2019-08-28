import subprocess
import importlib.util

def install(packages: list):
    """Installs pip packages.
    
    Arguments:
        packages {list} -- List of pip packages.
    """
    
    for p in packages:
        if not importlib.util.find_spec(p):
            subprocess.run(['pip3', 'install', '--upgrade', p])
