"""Deprecated alias for the ``nodepy`` package.

``from Engine.Node import Node`` keeps working and returns the very same
class as ``from nodepy.Node import Node``.  Switch to ``nodepy``; this alias
will be removed in a future release.
"""

import importlib
import pkgutil
import sys
import warnings

import nodepy

warnings.warn(
    "The 'Engine' package has been renamed to 'nodepy'; "
    "update your imports (e.g. 'from nodepy.Node import Node').",
    DeprecationWarning,
    stacklevel=2,
)

__version__ = nodepy.__version__

# Point every Engine.<Module> at the real nodepy.<Module> so classes, class
# attributes (Camera2D._active, Node._deferred_free_queue, ...) are shared.
# Engine.<Module> stays a module, exactly as before the rename.
for _info in pkgutil.iter_modules(nodepy.__path__):
    _module = importlib.import_module(f"nodepy.{_info.name}")
    sys.modules[f"{__name__}.{_info.name}"] = _module
    globals()[_info.name] = _module
