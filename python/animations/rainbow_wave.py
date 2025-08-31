from typing import Tuple

import numpy as np


GridSize = 64


def _hsv_to_rgb(h: np.ndarray, s: np.ndarray, v: np.ndarray) -> np.ndarray:
    h = np.mod(h, 1.0) * 6.0
    i = np.floor(h).astype(int)
    f = h - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))

    r = np.select(
        [i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [v, q, p, p, t, v], default=v
    )
    g = np.select(
        [i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [t, v, v, q, p, p], default=v
    )
    b = np.select(
        [i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [p, p, t, v, v, q], default=v
    )

    rgb = np.stack([r, g, b], axis=-1)
    return np.clip(rgb * 255.0, 0, 255).astype(np.uint8)


def rainbow_wave(frame_index: int, t_seconds: float) -> np.ndarray:
    y, x = np.mgrid[0:GridSize, 0:GridSize]
    hue = (x / GridSize + t_seconds * 0.1) % 1.0
    sat = np.ones_like(hue)
    val = 0.6 + 0.4 * np.sin(2 * np.pi * (y / GridSize + t_seconds * 0.25))
    val = np.clip(val, 0.0, 1.0)
    return _hsv_to_rgb(hue, sat, val)
