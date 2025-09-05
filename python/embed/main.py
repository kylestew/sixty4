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

# Pre-computed 8x8 Bayer dither matrix (scaled to 0-240 range) - COMMENTED OUT
# DITHER_W = const(8)   # assuming an 8×8 Bayer matrix
# DITHER_H = const(8)
# bayer8 = bytes([
#      0, 128,  32, 160,   8, 136,  40, 168,
#     192,  64, 224,  96, 200,  72, 232, 104,
#      48, 176,  16, 144,  56, 184,  24, 152,
#     240, 112, 208,  80, 248, 120, 216,  88,
#      12, 140,  44, 172,   4, 132,  36, 164,
#     204,  76, 236, 108, 196,  68, 228, 100,
#      60, 188,  28, 156,  52, 180,  20, 148,
#     252, 124, 220,  92, 244, 116, 212,  84,
# ])

# Pre-computed 4x4 Bayer dither matrix (scaled to 0-255 range)
DITHER_W = const(4)  # 4×4 Bayer matrix
DITHER_H = const(4)
bayer8 = bytes(
    [
        0,
        128,
        32,
        160,
        192,
        64,
        224,
        96,
        48,
        176,
        16,
        144,
        240,
        112,
        208,
        80,
    ]
)


@micropython.viper
def make_dither_ptr() -> ptr8:  # noqa: F821
    return ptr8(bayer8)  # noqa: F821


dither_ptr = make_dither_ptr()


@micropython.viper
def bit_shift_down(buf: ptr32, lines: int):  # noqa: F821
    """
    Copy rows downward by 1, starting at y=HEIGHT-2 down to y=lines-1.
    Row 'lines' will receive the previous 'lines-1' (the last drawn row).
    """
    row_bytes: int = WIDTH * 3
    row_words: int = row_bytes >> 2  # 64*3 = 192 -> 48 words

    # y: HEIGHT-2, ..., lines-1
    for y in range(HEIGHT - 2, int(lines) - 2, -1):
        src_w: int = int(y) * row_words
        dst_w: int = int(y + 1) * row_words
        for w in range(row_words):
            buf[dst_w + w] = buf[src_w + w]


def clamp01(x): 
    return x
    # return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def write_pattern(
    frame_index: int, ticks_ms: float, frame: memoryview, width: int
) -> None:
    """
    THE MAIN EVENT - generates the visuals

    ticks_ms is integer milliseconds
    """

    # animation params
    t = ticks_ms * 0.001            # seconds
    freq = 0.25                     # Hz
    omega = 2.0 * math.pi * freq
    amp, bias = 0.5, 0.5            # keep values in [0,1]

    s = math.sin(omega * t)
    stop0 = clamp01(bias + amp * s)     # left endpoint
    stop1 = clamp01(bias - amp * s)     # right endpoint (inverse phase)

    height = len(frame) // (width * 3)
    for x in range(width):

        # interpolate graident stops
        pct = x / (width - 1)   # range [0,1]
        val = stop0 + (stop1 - stop0) * pct
        grey = int(val * 255)

        for y in range(height):
            idx = (y * width + x) * 3

            frame[idx] = grey
            frame[idx + 1] = grey
            frame[idx + 2] = grey


@micropython.viper
def dither(frame: ptr8, dither_ptr: ptr8, height: int, width: int):  # noqa: F821
    """
    Converts frame contents to greyscale and applys bayer dithering
    """
    for y in range(height):
        row_base: int = y * width
        my: int = y % DITHER_H

        for x in range(width):
            idx: int = (row_base + x) * 3

            # Pull RGB directly from frame_buffer
            r: int = frame[idx]
            g: int = frame[idx + 1]
            b: int = frame[idx + 2]

            # integer-luma approx: Y ≈ 0.299R + 0.587G + 0.114B
            # 77/150/29 are 256 * coefficients, then >> 8
            gray: int = (r * 77 + g * 150 + b * 29) >> 8

            # lookup Bayer threshold
            mx: int = x % DITHER_W
            m_idx: int = my * DITHER_W + mx
            thresh: int = dither_ptr[m_idx]

            # apply threshold and write back as monochrome RGB
            v: int = 255 if gray > thresh else 0
            frame[idx] = v
            frame[idx + 1] = v
            frame[idx + 2] = v


@micropython.viper
def blit(frame: ptr8, graphics: ptr32, brightness: int):  # noqa: F821
    for y in range(HEIGHT):
        base: int = y * WIDTH * 3  # 3 bytes per pixel
        dx: int = y  # rotated x' = y

        for x in range(WIDTH):
            idx: int = base + x * 3

            # Pull RGB directly from frame_buffer
            r: int = frame[idx]
            g: int = frame[idx + 1]
            b: int = frame[idx + 2]

            # Apply brightness scaling (fixed-point >> 8)
            r: int = (r * brightness) >> 8
            g: int = (g * brightness) >> 8
            b: int = (b * brightness) >> 8

            # Clamp to 255
            if r > 255:
                r = 255
            if g > 255:
                g = 255
            if b > 255:
                b = 255

            # Pack into 0xRRGGBB (24-bit in 32-bit slot)
            val: int = (r << 16) | (g << 8) | b

            # Rotate 90° clockwise
            dy: int = WIDTH - 1 - x
            d_idx: int = dy * HEIGHT + dx

            graphics[d_idx] = val


t_frames = 0
start_time = time.ticks_ms()

while True:
    # time is ticked in ms, integer
    t_start = time.ticks_ms()
    current_time = time.ticks_diff(t_start, start_time)

    # === MASK + WRITE ===
    # slice a section of the output buffer and write pattern to it
    lines = 20
    sz_data = lines * WIDTH * 3  # r,g,b
    region = memoryview(frame_buffer)[:sz_data]
    write_pattern(t_frames, current_time, region, WIDTH)

    # === DITHER ===
    dither(region, dither_ptr, HEIGHT, WIDTH)

    # === BIT SHIFT ===
    # Shift existing content before writing new pattern
    bit_shift_down(memoryview(frame_buffer), lines)

    # === BLIT ===
    # send internal frame buffer to output (rotated)
    blit(memoryview(frame_buffer), memoryview(graphics), 192)
    i75.update()

    # pause for a moment (important or the USB serial device will fail)
    time.sleep(0.03)

    t_frames += 1
