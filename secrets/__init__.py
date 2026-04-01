""" this init contains validation for the local configs for picoSysmon.py """
import os
import sys

from . import CONFIG

# We won't export any functions, just some variable definitions
__all__ = [
    '',
]

lconfig_name = "CONFIG_local"
package_name = __name__

# Get the directory of this package
try:
    full_module_path = f"{package_name}.{lconfig_name}"
    __import__(full_module_path)
    lvars = sys.modules[full_module_path]

    # Iterate over the CONFIG_local module, inserting or replacing values as found
    for key in dir(lvars):
        if not key.startswith("_"):
            value = getattr(lvars, key)
            setattr(CONFIG, key, value)

except (ImportError, KeyError):
    # If CONFIG_local.py does not exist, do nothing
    pass
