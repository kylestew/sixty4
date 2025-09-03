import numpy as np


def dithered_sine_wave(frame_index: int, t_seconds: float, out: np.ndarray) -> None:
    """Fill top N rows with dithered gradient pattern, shift content down over time.

    - Creates horizontal gradient between two animated color stops
    - Each stop evolves from black to white using triangle waves (different phases)
    - Uses ordered dithering to convert greyscale gradient to B/W pattern
    - Shifts existing content down like cascading dots effect
    """
    h, w, _ = out.shape
    if h == 0 or w == 0:
        return

    N = 20  # Number of top rows to reserve for dithered pattern

    # Shift down rows N and below to avoid moving the newly drawn band
    if N < h:
        out[N:, :, :] = out[N - 1 : -1, :, :]

    # Generate triangle wave values for left and right color stops
    triangle_period = 6.0  # seconds for full cycle

    # Left stop: starts at phase 0
    t_left = (t_seconds % triangle_period) / triangle_period
    left_value = 1.0 - 2.0 * abs(t_left - 0.5)  # 0.0 to 1.0
    left_grey = int(left_value * 255)

    # Right stop: starts at phase 0.5 (opposite phase)
    t_right = ((t_seconds + triangle_period * 0.5) % triangle_period) / triangle_period
    right_value = 1.0 - 2.0 * abs(t_right - 0.5)  # 0.0 to 1.0
    right_grey = int(right_value * 255)

    # Create horizontal gradient between the two stops
    x_coords = np.arange(w, dtype=np.float32)
    x_normalized = (
        x_coords / (w - 1) if w > 1 else np.zeros_like(x_coords)
    )  # 0.0 to 1.0

    # Linear interpolation between left and right stops
    gradient_values = left_grey * (1.0 - x_normalized) + right_grey * x_normalized
    gradient_values = gradient_values.astype(np.uint8)

    # Create 4x4 ordered dithering matrix (Bayer matrix)
    dither_matrix = (
        np.array(
            [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]],
            dtype=np.uint8,
        )
        * 16
    )  # Scale to 0-240 range

    # Create coordinate grids for top N rows only
    y_coords, x_coords_2d = np.mgrid[0:N, 0:w]

    # Get dither threshold for each pixel based on position
    dither_y = y_coords % 4
    dither_x = x_coords_2d % 4
    threshold = dither_matrix[dither_y, dither_x]

    # Expand gradient to all N rows and apply dithering
    gradient_2d = np.broadcast_to(gradient_values[np.newaxis, :], (N, w))
    is_white = gradient_2d > threshold

    # Set output colors for top N rows only
    out[0:N, :, 0] = np.where(is_white, 255, 0)  # Red
    out[0:N, :, 1] = np.where(is_white, 255, 0)  # Green
    out[0:N, :, 2] = np.where(is_white, 255, 0)  # Blue
