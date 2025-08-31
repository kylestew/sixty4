import numpy as np


def simple_noise(frame_index: int, t_seconds: float, out: np.ndarray) -> None:
    """Fill the output buffer with a simple procedural grayscale noise field.

    Uses a fast hash on (x, y, frame_index) to avoid large temporary allocations.
    """
    h, w, _ = out.shape
    if h == 0 or w == 0:
        return

    # Coordinate grids
    y, x = np.mgrid[0:h, 0:w]

    # Hash-based value noise per pixel; varies with frame_index
    n = (x.astype(np.uint64) * 374761393) ^ (y.astype(np.uint64) * 668265263)
    n ^= np.uint64(frame_index) * np.uint64(2246822519)
    n = (n ^ (n >> np.uint64(13))) * np.uint64(1274126177)
    n = n ^ (n >> np.uint64(16))

    gray = (n & np.uint64(255)).astype(np.uint8)
    out[..., 0] = gray
    out[..., 1] = gray
    out[..., 2] = gray
