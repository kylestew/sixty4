import numpy as np


GridSize = 64


def bouncing_dot(frame_index: int, t_seconds: float) -> np.ndarray:
    img = np.zeros((GridSize, GridSize, 3), dtype=np.uint8)
    px = int((np.sin(t_seconds * 1.3) * 0.5 + 0.5) * (GridSize - 1))
    py = int((np.cos(t_seconds * 1.9) * 0.5 + 0.5) * (GridSize - 1))
    img[py, px] = (255, 220, 64)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            yy = np.clip(py + dy, 0, GridSize - 1)
            xx = np.clip(px + dx, 0, GridSize - 1)
            if dy == 0 and dx == 0:
                continue
            img[yy, xx] = (64, 64, 64)
    return img
