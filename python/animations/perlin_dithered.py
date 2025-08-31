import numpy as np

from . import perlin as _perlin


# https://formandstructure.co/notes/dithering

# 4x4 Bayer matrix thresholds in [0,1]
_BAYER_4x4 = (1.0 / 16.0) * np.array(
    [
        [0, 8, 2, 10],
        [12, 4, 14, 6],
        [3, 11, 1, 9],
        [15, 7, 13, 5],
    ],
    dtype=np.float32,
)
_BAYER_4x4 = (_BAYER_4x4 + (0.5 / 16.0)).astype(np.float32)


def perlin_dithered(frame_index: int, t_seconds: float, out: np.ndarray) -> None:
    """Perlin noise with ordered Bayer dithering to produce a 1-bit look.

    Writes white where noise exceeds the local threshold; black otherwise.
    """
    h, w, _ = out.shape
    if h == 0 or w == 0:
        return

    # Sample perlin noise (reuse same params as perlin.perlin_noise)
    freq = 0.08
    xoff = t_seconds * 0.25
    yoff = t_seconds * 0.18

    y, x = np.mgrid[0:h, 0:w]
    xs = x * freq + xoff
    ys = y * freq + yoff

    n = _perlin._perlin2(xs, ys)  # [0,1]

    # Tile Bayer thresholds to image size
    th = np.tile(_BAYER_4x4, (int(np.ceil(h / 4)), int(np.ceil(w / 4))))[:h, :w]

    mask = n > th
    out[:] = 0
    out[mask, 0] = 255
    out[mask, 1] = 255
    out[mask, 2] = 255
