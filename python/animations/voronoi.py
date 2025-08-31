import numpy as np


_rng = np.random.default_rng(42)
_NUM_SEEDS = 24
_SEED_BASE = _rng.random((_NUM_SEEDS, 2))  # in [0,1) for (y, x)
_SEED_DIR = _rng.normal(size=(_NUM_SEEDS, 2))
_SEED_DIR /= np.linalg.norm(_SEED_DIR, axis=1, keepdims=True) + 1e-9


def _animated_seed_positions(h: int, w: int, t: float) -> np.ndarray:
    # Lissajous-like motion per seed
    speed = 0.2
    amp = 0.35  # fraction of dimension
    phase = np.array([t * speed, t * speed * 1.31])
    offs = np.sin(phase)  # shape (2,)
    pos = _SEED_BASE + amp * _SEED_DIR * offs  # broadcast (N,2) * (2,) -> (N,2)
    # Wrap to [0,1]
    pos = pos - np.floor(pos)
    pos[:, 0] *= float(h - 1)
    pos[:, 1] *= float(w - 1)
    return pos  # (N,2) in pixel coords (y, x)


def voronoi_noise(frame_index: int, t_seconds: float, out: np.ndarray) -> None:
    """Voronoi (cellular) noise as grayscale.

    Shades by distance to nearest moving seed. Animated by drifting the seeds.
    """
    h, w, _ = out.shape
    if h == 0 or w == 0:
        return

    y, x = np.mgrid[0:h, 0:w]
    y = y.astype(np.float32)
    x = x.astype(np.float32)

    seeds = _animated_seed_positions(h, w, t_seconds).astype(np.float32)

    # Compute nearest seed distance (squared) for each pixel
    min_d2 = np.full((h, w), np.float32(1e9))
    for sy, sx in seeds:
        dy = y - sy
        dx = x - sx
        d2 = dy * dy + dx * dx
        np.minimum(min_d2, d2, out=min_d2)

    # Normalize by maximal possible distance (diagonal)
    max_d2 = (h - 1) * (h - 1) + (w - 1) * (w - 1)
    n = np.sqrt(min_d2 / max(max_d2, 1.0))  # [0,1]

    # Increase contrast and boost edges with a gamma curve
    n = 1.0 - np.clip(n * 2.0, 0.0, 1.0)
    n = np.power(n, 0.6)
    gray = (n * 255.0).astype(np.uint8)
    out[..., 0] = gray
    out[..., 1] = gray
    out[..., 2] = gray
