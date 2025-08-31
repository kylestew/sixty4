import numpy as np


def _smoothstep(edge0: float, edge1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - edge0) / max(edge1 - edge0, 1e-6), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def sdf_sphere(frame_index: int, t_seconds: float, out: np.ndarray) -> None:
    """Animated 2D SDF "sphere" (circle) with glowing rim and soft interior.

    - Center drifts over time; radius gently pulses.
    - Writes grayscale into the reusable out buffer (H, W, 3) uint8.
    """
    h, w, _ = out.shape
    if h == 0 or w == 0:
        return

    # Normalized coordinates in [-1, 1], aspect-corrected
    y, x = np.mgrid[0:h, 0:w]
    sx = (x - (w - 1) * 0.5) / max(w, h)
    sy = (y - (h - 1) * 0.5) / max(w, h)

    # Animated center and radius
    cx = 0.35 * np.sin(t_seconds * 0.7)
    cy = 0.28 * np.cos(t_seconds * 0.9)
    r = 0.42 + 0.10 * np.sin(t_seconds * 0.5)

    # Signed distance to circle (negative inside)
    d = np.sqrt((sx - cx) ** 2 + (sy - cy) ** 2) - r

    # Bright rim near the surface using a thin band around d=0
    rim_thickness = 0.02
    rim = 1.0 - _smoothstep(0.0, rim_thickness, np.abs(d))

    # Soft interior fill based on normalized inside distance
    interior = np.clip((-d) / max(r, 1e-6), 0.0, 1.0)

    # Combine rim and interior; weight rim higher for a crisp edge
    intensity = np.clip(0.75 * interior + 0.85 * rim, 0.0, 1.0)

    gray = (intensity * 255.0).astype(np.uint8)
    out[..., 0] = gray
    out[..., 1] = gray
    out[..., 2] = gray
