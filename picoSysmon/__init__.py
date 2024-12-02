"""Main module for picoSysmon"""

from . import picoSysmon

# We only export the 'run' function, everything else is internal!
__all__ = [
    'run',
]
