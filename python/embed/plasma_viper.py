import time
import machine  # noqa: F401
import micropython
import math
from array import array
from micropython import const
from interstate75 import Interstate75, DISPLAY_INTERSTATE75_128X64

"""
Plasma effect for Interstate75 128x64 display.
Generates a smooth animated plasma using lookup tables for speed.
"""

# Runs ~30fps with stock clock,

# uncomment the below for ~40fps
# machine.freq(200_000_000)

# uncomment the below for ~50fps
# machine.freq(250_000_000)

# Setup for the display
i75 = Interstate75(
    display=DISPLAY_INTERSTATE75_128X64,
    stb_invert=False,
    panel_type=Interstate75.PANEL_GENERIC,
)
graphics = i75.display

# Constants for viper optimized blocks
WIDTH = const(128)
HEIGHT = const(64)

ANGLE_STEPS = const(1024)  # sine table resolution (must be power of two)
ANGLE_MASK = const(ANGLE_STEPS - 1)

# Angle multipliers for different sine components (higher = smaller features)
ANGLE_X1 = const(9)
ANGLE_Y1 = const(11)
ANGLE_XY = const(13)
ANGLE_XmY = const(8)


def _hsv_to_rgb24(h: float, s: float, v: float) -> int:
    if s <= 0.0:
        c = int(v * 255)
        return (c << 16) | (c << 8) | c
    h = (h % 1.0) * 6.0
    i = int(h)
    f = h - i
    p = int(255 * v * (1.0 - s))
    q = int(255 * v * (1.0 - s * f))
    t = int(255 * v * (1.0 - s * (1.0 - f)))
    v = int(255 * v)
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    return (r << 16) | (g << 8) | b


# Precompute a sine lookup table [0..255] for ANGLE_STEPS samples
_sin_table = bytearray(ANGLE_STEPS)
for i in range(ANGLE_STEPS):
    _sin_table[i] = int(128 + 127 * math.sin(2.0 * math.pi * (i / ANGLE_STEPS)))


# Precompute a 256-colour palette cycling the hue
_palette_list = [_hsv_to_rgb24(i / 256.0, 1.0, 1.0) for i in range(256)]
_palette = array("I", _palette_list)


@micropython.viper
def _make_sin_ptr() -> ptr8:  # noqa: F821
    return ptr8(_sin_table)  # noqa: F821


@micropython.viper
def _make_palette_ptr() -> ptr32:  # noqa: F821
    return ptr32(_palette)  # noqa: F821


@micropython.viper
def draw_plasma(
    t1: int, t2: int, t3: int, t4: int, palette: ptr32, sin_table: ptr8, graphics: ptr32
):  # noqa: F821
    for y in range(HEIGHT):
        base_y = y * WIDTH
        y_term1 = (y * ANGLE_Y1 + t2) & ANGLE_MASK
        y_term2 = (y * ANGLE_XmY + t4) & ANGLE_MASK
        for x in range(WIDTH):
            x_term1 = (x * ANGLE_X1 + t1) & ANGLE_MASK
            xy_term = ((x + y) * ANGLE_XY + t3) & ANGLE_MASK
            xm_y_term = (x * ANGLE_XmY - y_term2) & ANGLE_MASK

            s1 = int(sin_table[x_term1])
            s2 = int(sin_table[y_term1])
            s3 = int(sin_table[xy_term])
            s4 = int(sin_table[xm_y_term])

            idx = (s1 + s2 + s3 + s4) >> 2  # 0..255
            colour = palette[idx]
            graphics[x + base_y] = colour


sin_ptr = _make_sin_ptr()
palette_ptr = _make_palette_ptr()

t_total = 0
t_frames = 0
t1 = 0
t2 = 0
t3 = 0
t4 = 0

while True:
    t_start = time.ticks_ms()

    draw_plasma(t1, t2, t3, t4, palette_ptr, sin_ptr, memoryview(graphics))
    i75.update()

    # Advance phase and pause briefly (important for USB stability)
    t1 = (t1 + 3) & ANGLE_MASK
    t2 = (t2 + 5) & ANGLE_MASK
    t3 = (t3 + 7) & ANGLE_MASK
    t4 = (t4 + 11) & ANGLE_MASK
    time.sleep(0.001)

    t_end = time.ticks_ms()

    t_total += time.ticks_diff(t_end, t_start)
    t_frames += 1

    if t_frames == 100:
        per_frame_avg = t_total / t_frames
        print(
            f"100 frames in {t_total}ms, avg {per_frame_avg:.02f}ms per frame, {1000 / per_frame_avg:.02f} FPS"
        )
        t_frames = 0
        t_total = 0
