"""Animations package.

Expose ANIMATIONS as a list of (name, frame_func) tuples. On reload, also
reload submodules to reflect changes without restarting the app.
"""

from typing import List, Tuple, Callable
import importlib

import numpy as np  # Re-exported type only

from . import rainbow_wave as _rainbow_wave
from . import bouncing_dot as _bouncing_dot
from . import plasma as _plasma

# Ensure submodules are reloaded when this package is reloaded
for _mod in (_rainbow_wave, _bouncing_dot, _plasma):
    try:
        importlib.reload(_mod)
    except Exception:
        # Fallback: keep existing definitions if reload fails
        pass

ANIMATIONS: List[Tuple[str, Callable[[int, float, np.ndarray], None]]] = [
    ("Rainbow Wave", _rainbow_wave.rainbow_wave),
    ("Bouncing Dot", _bouncing_dot.bouncing_dot),
    ("Plasma", _plasma.plasma),
]

__all__ = ["ANIMATIONS"]
