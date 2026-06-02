"""
blick_utils - A collection of utility functions
"""

__version__ = "26.6.2"

from .core import BlickUtils

# Dynamically expose all static methods:
for name in dir(BlickUtils):
    attr = getattr(BlickUtils, name)
    if callable(attr):
        globals()[name] = attr
