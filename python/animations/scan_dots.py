# from turtle import down
import numpy as np


def cascading_dots(frame_index: int, t_seconds: float, out: np.ndarray) -> None:
    """Shift rows at index N and below down by one; draw random dots on top N rows.

    - Does NOT clear the full buffer; content drifts downward over time.
    - Top row is refreshed each frame with a sparse set of white pixels.
    - Randomness is derived from (x, frame_index) via a hash to avoid RNG state.
    """
    h, w, _ = out.shape
    if h == 0 or w == 0:
        return

    # TODO: change the random section every T seconds but keep moving down
    # Make the random section larger

    # Draw a new random set of dots on the top N rows
    # Hash-based pseudo-random mask per (x,y), stable for a given frame_index
    N = 20
    X = 10  # Change every X frames
    x = np.arange(w, dtype=np.uint64)
    stable_frame = frame_index // X

    # Shift down only rows N and below to avoid moving the newly drawn band
    if N < h:
        out[N:, :, :] = out[N - 1 : -1, :, :]

    # Clear top N rows
    out[0:N, :, :] = 0

    # Generate unique random pattern for each row
    for y in range(N):
        n = (x * np.uint64(374761393)) ^ (
            np.uint64(stable_frame + y) * np.uint64(668265263)
        )
        n ^= (n >> np.uint64(13)) * np.uint64(1274126177)
        n ^= n >> np.uint64(16)
        mask = (n & np.uint64(255)) < np.uint64(64)  # ~25% density

        out[y, mask, 0] = 255
        out[y, mask, 1] = 255
        out[y, mask, 2] = 255
