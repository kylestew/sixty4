import time
import machine  # noqa: F401
import random
import micropython
from micropython import const
from interstate75 import Interstate75, DISPLAY_INTERSTATE75_128X64
#from picographics import PicoGraphics, DISPLAY_INTERSTATE75_128X64, PEN_RGB888
#import hub75

i75 = Interstate75(
    display=DISPLAY_INTERSTATE75_128X64,
    stb_invert=False,
    panel_type=Interstate75.PANEL_GENERIC,
)
graphics = i75.display

DISPLAY_WIDTH = const(128)
DISPLAY_HEIGHT = const(64)
WIDTH = const(64)
HEIGHT = const(128)

"""
# init from Interstate75 module
# https://github.com/pimoroni/interstate75/blob/main/modules/rp2350/interstate75.py

# rotation support!
# https://github.com/pimoroni/pimoroni-pico/tree/main/micropython/modules/picographics
buffer = PicoGraphics(display=DISPLAY_INTERSTATE75_128X64, pen_type=PEN_RGB888, rotate=90)
matrix = hub75.Hub75(WIDTH, HEIGHT, panel_type=hub75.PANEL_GENERIC, stb_invert=False, color_order=hub75.COLOR_ORDER_RGB)
matrix.start()
"""


# SIMPLE SIMPLE STATE
# 0 = empty
# 1 = sand
sand_array = bytearray(HEIGHT * WIDTH)

emit_x_pos = WIDTH // 2

@micropython.viper
def make_sand() -> ptr8:  # noqa: F821
    return ptr8(sand_array)  # noqa: F821


@micropython.viper
def get_index(x: int, y: int) -> int:
    if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
        return -1
    return y * WIDTH + x


@micropython.viper
def emit(sand: ptr8):
    global emit_x_pos
    # ~1/3 chance to step this frame
    if random.random() < 0.333:
        step = int(random.randint(-1, 1))
        emit_x_pos = (int(emit_x_pos) + step) % WIDTH  # ← wrap across width
        idx = int(get_index(emit_x_pos, 0))
        if idx >= 0:
            sand[idx] = 1


@micropython.viper
def step(sand: ptr8):  # noqa: F821
    # iterate bottom to top, right to left; skip last row (static)
    for y in range(HEIGHT - 2, -1, -1):
        for x in range(WIDTH - 1, -1, -1):
            idx = int(get_index(x, y))
            # cell in bounds and not empty
            if idx >= 0 and sand[idx] != 0:
                below_idx = int(get_index(x, y + 1))
                if below_idx == -1:
                    continue  # at the bottom
                left_idx = int(get_index(x - 1, y + 1))
                right_idx = int(get_index(x + 1, y + 1))
                rule_fn(idx, below_idx, left_idx, right_idx, sand)

@micropython.viper
def rule_fn(idx: int, below_idx: int, left_idx: int, right_idx: int, sand: ptr8): # noqa: F821
    """
    Apply sand rules for a single cell using the sand buffer directly.
    Indices may be -1 to indicate out-of-bounds.
    """
    # Rule 1: fall straight down if empty
    if below_idx > -1 and sand[below_idx] == 0:
        tmp = sand[idx]
        sand[idx] = sand[below_idx]
        sand[below_idx] = tmp
        return

    # Randomize diagonal direction
    if bool(random.getrandbits(1)):
        left_idx, right_idx = right_idx, left_idx

    # Rule 2: fall down-left if empty
    if left_idx > -1 and sand[left_idx] == 0:
        tmp = sand[idx]
        sand[idx] = sand[left_idx]
        sand[left_idx] = tmp
        return

    # Rule 3: fall down-right if empty
    if right_idx > -1 and sand[right_idx] == 0:
        tmp = sand[idx]
        sand[idx] = sand[right_idx]
        sand[right_idx] = tmp


@micropython.viper
def draw(sand: ptr8, graphics: ptr32):  # noqa: F821
    for y in range(HEIGHT):
        base = y * WIDTH
        for x in range(WIDTH):
            idx = base + x
            val = 0xFFFFFF if sand[idx] != 0 else 0x000000
             
            # rotate 90deg clockwise (screen is horizontal but sand field isn't)
            dx = y
            dy = DISPLAY_HEIGHT - 1 - x
            d_idx = dy * DISPLAY_WIDTH + dx

            graphics[d_idx] = val


sand = make_sand()

while True:
    # t_start = time.ticks_ms()
    
    emit(sand)
    step(sand)
    draw(sand, memoryview(graphics))

    i75.update()

    # pause for a moment (important or the USB serial device will fail)
    time.sleep(0.0333) # 30 fps


