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
from . import noise as _noise
from . import perlin as _perlin
from . import voronoi as _voronoi
from . import scan_dots as _scan_dots
from . import perlin_dithered as _perlin_dithered
from . import sdf_sphere as _sdf_sphere

# Ensure submodules are reloaded when this package is reloaded
for _mod in (
    _rainbow_wave,
    _bouncing_dot,
    _plasma,
    _noise,
    _perlin,
    _voronoi,
    _scan_dots,
    _perlin_dithered,
    _sdf_sphere,
):
    try:
        importlib.reload(_mod)
    except Exception:
        # Fallback: keep existing definitions if reload fails
        pass

ANIMATIONS: List[Tuple[str, Callable[[int, float, np.ndarray], None]]] = [
    ("Cascading Dots", _scan_dots.cascading_dots),
    ("Rainbow Wave", _rainbow_wave.rainbow_wave),
    ("Bouncing Dot", _bouncing_dot.bouncing_dot),
    ("Plasma", _plasma.plasma),
    ("Noise", _noise.simple_noise),
    ("Perlin Noise", _perlin.perlin_noise),
    ("Voronoi", _voronoi.voronoi_noise),
    ("Perlin Dithered", _perlin_dithered.perlin_dithered),
    ("SDF Sphere", _sdf_sphere.sdf_sphere),
]

__all__ = ["ANIMATIONS"]
