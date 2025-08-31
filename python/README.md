### 64x128 LED Animation Prototyper (Pygame)

Prototype RGB LED matrix animations with oversized pixels. Default grid is 64x128, pixels scaled 12x, with a hot-reloadable animations package.

### Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run
```bash
python led_animator.py
```

Optional environment overrides:
```bash
# grid size (width/height) – defaults to 64x128
LED_GRID_WIDTH=64 LED_GRID_HEIGHT=128 \
# legacy single-size (applies to both width/height)
LED_GRID_SIZE=64 \
# pixel scaling and target FPS
LED_PIXEL_SCALE=12 LED_TARGET_FPS=60 \
python led_animator.py
```

### Controls
- SPACE: Play/Pause
- LEFT/RIGHT: Previous/Next animation
- UP/DOWN: Speed +/- 25%
- G: Toggle grid overlay
- R: Force reload animations
- Q or ESC: Quit

### Add Animations
Animations live in the `animations/` package and are hot-reloaded.

1) Create a new file like `animations/my_anim.py`:
```python
import numpy as np

def my_anim(frame_i: int, t: float, out: np.ndarray) -> None:
    # out is a reusable (H, W, 3) uint8 buffer. Write in-place.
    out.fill(0)
    h, w, _ = out.shape
    out[h//2, w//2] = (255, 128, 0)
```

2) Register it in `animations/__init__.py`:
```python
from . import my_anim as _my_anim
import importlib; importlib.reload(_my_anim)
ANIMATIONS.append(("My Anim", _my_anim.my_anim))
```

Save the files; the app will reload automatically.

### Notes
- A single frame buffer is reused every frame (animations write in-place) for embedded-friendly behavior.
- The grid overlay is enabled by default and scales with pixel size.
