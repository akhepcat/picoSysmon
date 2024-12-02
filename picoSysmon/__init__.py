"""Main module for picoSysmon"""


from .picoSysmon import picoSysmon


# We only export the 'run' function, everything else is internal!
__all__ = [
    'run',
]
