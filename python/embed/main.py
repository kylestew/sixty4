import time
import machine  # noqa: F401
import micropython
import math
from micropython import const
from interstate75 import Interstate75, DISPLAY_INTERSTATE75_128X64

"""
Animation runner for Micropython / Hub displays
"""

# Setup for the display
i75 = Interstate75(
    display=DISPLAY_INTERSTATE75_128X64,
    stb_invert=False,
    panel_type=Interstate75.PANEL_GENERIC,
)
graphics = i75.display

# Constants for viper optimized blocks
WIDTH = const(64)  # internal size
HEIGHT = const(128)  # display driver is rotated 90

# Detached frame buffer: HEIGHT * WIDTH * 3 bytes
# Frame buffer is rotated 90 degrees
frame_buffer = bytearray(HEIGHT * WIDTH * 3)

# Pre-computed 4x4 Bayer dither matrix (scaled to 0-240 range)
_dither_matrix = bytearray(
    [0, 128, 32, 160, 192, 64, 224, 96, 48, 176, 16, 144, 240, 112, 208, 80]
)


# No frame buffer needed - we'll shift content in-place


# @micropython.viper
# def make_dither_ptr() -> ptr8:  # noqa: F821
#     return ptr8(_dither_matrix)  # noqa: F821


# Buffer pointer no longer needed


# @micropython.viper
# def triangle_wave(t_ms: int, period_ms: int, phase_offset: int) -> int:
#    """Generate triangle wave value 0-255 for given time and period"""
#     # Add phase offset (in ms)
#     t_phase = (t_ms + phase_offset) % period_ms
#     # Normalize to 0.0 - 1.0
#     t_norm = t_phase / period_ms
#     # Triangle wave: 0 -> 1 -> 0
#     if t_norm <= 0.5:
#         wave_val = 2.0 * t_norm
#     else:
#         wave_val = 2.0 * (1.0 - t_norm)
#     return int(wave_val * 255)


@micropython.viper
def shift_content_down(graphics_ptr: ptr32):  # noqa: F821
    pass


#     """Shift existing content down by one row"""
#     # Shift rows N_ROWS to HEIGHT-2 down to rows N_ROWS+1 to HEIGHT-1
#     # Work from bottom up to avoid overwriting data we still need to copy
#     for y in range(HEIGHT - 2, N_ROWS - 1, -1):
#         src_row_start = int(y) * int(WIDTH)
#         dst_row_start = (y + 1) * WIDTH
#         for x in range(WIDTH):
#             graphics_ptr[dst_row_start + x] = graphics_ptr[src_row_start + x]


# @micropython.viper
# def draw_dithered_rows(
#     left_grey: int, right_grey: int, dither_ptr: ptr8, graphics_ptr: ptr32
# ):  # noqa: F821
#     """Draw dithered gradient in top N_ROWS rows"""
#     for y in range(N_ROWS):
#         graphics_row_start = y * WIDTH
#         dither_y = y & 3  # y % 4
#
#         for x in range(WIDTH):
#             # Linear interpolation between left and right grey values
#             if WIDTH > 1:
#                 x_norm = x / (WIDTH - 1)
#             else:
#                 x_norm = 0
#             gradient_val = int(left_grey * (1.0 - x_norm) + right_grey * x_norm)
#
#             # Get dither threshold from 4x4 matrix
#             dither_x = x & 3  # x % 4
#             dither_idx = dither_y * 4 + dither_x
#             threshold = int(dither_ptr[dither_idx])
#
#             # Apply dithering: white if gradient > threshold, else black
#             if gradient_val > threshold:
#                 color = 0xFFFFFF  # White
#             else:
#                 color = 0x000000  # Black
#
#             graphics_ptr[graphics_row_start + x] = color


def write_pattern(frame_index: int, t_seconds: float, frame: memoryview, width: int) -> None:
    """
    t_seconds is integer milliseconds
    """
    height = len(frame) // (width * 3)

    grey = int(t_seconds * 0.01) % 256

    for y in range(height):
        for x in range(width):
            idx = (y * width + x) * 3

            # r = (x + int(t_seconds * 30)) % 256
            # g = (y + int(t_seconds * 60)) % 256
            # b = (frame_index * 2) % 256

            frame[idx] = grey
            frame[idx + 1] = grey
            frame[idx + 2] = grey


@micropython.viper
def blit(frame: ptr8, graphics: ptr32):  # noqa: F821
    for y in range(HEIGHT):
        base: int = y * WIDTH * 3  # 3 bytes per pixel
        dx: int = y  # rotated x' = y

        for x in range(WIDTH):
            idx: int = base + x * 3

            # Pull RGB directly from frame_buffer
            r: int = frame[idx]
            g: int = frame[idx + 1]
            b: int = frame[idx + 2]

            # Pack into 0xRRGGBB (24-bit in 32-bit slot)
            val: int = (r << 16) | (g << 8) | b

            # Rotate 90° clockwise
            dy: int = WIDTH - 1 - x
            d_idx: int = dy * HEIGHT + dx

            graphics[d_idx] = val


# dither_ptr = make_dither_ptr()

t_frames = 0
start_time = time.ticks_ms()

while True:
    # time is ticked in ms, integer
    t_start = time.ticks_ms()
    current_time = time.ticks_diff(t_start, start_time)

    # MAIN RENDER FUNCTION
    # # Generate triangle wave values for left and right color stops
    # left_grey = triangle_wave(current_time, TRIANGLE_PERIOD_MS, 0)
    # right_grey = triangle_wave(
    #     current_time, TRIANGLE_PERIOD_MS, TRIANGLE_PERIOD_MS // 2
    # )

    # === BIT SHIFT ===
    # Shift existing content before writing new pattern
    # shift_content_down(memoryview(graphics))

    # === MASK + WRITE ===
    # slice a section of the output buffer and write pattern to it
    lines = 20
    sz_data = lines * WIDTH * 3 # r,g,b
    region = memoryview(frame_buffer)[:sz_data]
    write_pattern(t_frames, current_time, region, WIDTH)

    # TODO: convert to gradient pattern somehow

    # === BLIT ===
    # send internal frame buffer to output (rotated)
    blit(memoryview(frame_buffer), memoryview(graphics))

    i75.update()

    # pause for a moment (important or the USB serial device will fail)
    # time.sleep(0.001)

    time.sleep(0.1)
    t_frames += 1
