"""
TODO
"""
import importlib
import warnings

def alert_deprecated_import(import_path, raise_warning=True):
    """
    TODO
    """
    if raise_warning:
        warnings.warn("bad import (MESSAGE TODO)", DeprecationWarning)
