import numpy as np


GridSize = None  # unused; derive from output buffer


def bouncing_dot(frame_index: int, t_seconds: float, out: np.ndarray) -> None:
    out.fill(0)
    h, w, _ = out.shape
    px = int((np.sin(t_seconds * 1.3) * 0.5 + 0.5) * (w - 1))
    py = int((np.cos(t_seconds * 1.9) * 0.5 + 0.5) * (h - 1))
    out[py, px] = (255, 220, 64)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            yy = np.clip(py + dy, 0, h - 1)
            xx = np.clip(px + dx, 0, w - 1)
            if dy == 0 and dx == 0:
                continue
            out[yy, xx] = (64, 64, 64)
