""" this init contains validation for the secrets are in CONFIG.py """
import os
import sys

from . import CONFIG

# We won't export any functions, just some variable definitions
__all__ = [
    '',
]

lconfig = "CONFIG_local"

# Get the directory of this package
package_dir = __name__.rsplit('.', 1)[0]
overrides = f"{package_dir}.{lconfig}"

# Check for and dynamically load variables_local.py
try:
    lvars = __import__(overrides)

    # Override variables in the variables module
    for key in dir(lvars):
        if not key.startswith("_"):
            setattr(CONFIG, key, getattr(lvars, key))

except ImportError:
    # If variables_local.py does not exist, do nothing
    pass
