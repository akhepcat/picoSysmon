""" this init contains validation for the secrets are in CONFIG.py """
import os
import importlib.util

from . import CONFIG

# We won't export any functions, just some variable definitions
__all__ = [
    '',
]

lconfig = "CONFIG_local.py"

# Get the directory of this package
package_dir = os.path.dirname(os.path.abspath(__file__))
overrides = os.path.join(package_dir, lconfig)

# Check for and dynamically load variables_local.py
if os.path.exists(overrides):
    spec = importlib.util.spec_from_file_location(lconfig.replace(".py", ""), overrides)
    lvars = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lvars)

    # Override variables in the variables module
    for key, value in vars(lvars).items():
        if not key.startswith("_"):
            setattr(variables, key, value)

