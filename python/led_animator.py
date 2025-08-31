import os
import sys
import time
import importlib
import traceback
from types import ModuleType
from typing import Callable, List, Tuple, Optional

import numpy as np


try:
    import pygame
except Exception as exc:  # pragma: no cover - runtime import guard
    raise SystemExit(
        "pygame is required. Install dependencies with: pip install -r requirements.txt"
    ) from exc


GridFrameFunc = Callable[[int, float, np.ndarray], None]
AnimationTuple = Tuple[str, GridFrameFunc]


class AnimatorApp:
    """Simple 64x64 RGB LED animation prototyper with 8x pixel scaling and hot-reload.

    Controls:
    - SPACE: Play/Pause
    - LEFT/RIGHT: Previous/Next animation
    - UP/DOWN: Speed +/- 25%
    - G: Toggle grid overlay
    - R: Force reload animations
    - Q or ESC: Quit
    """

    def __init__(
        self,
        grid_width: int = 64,
        grid_height: int = 128,
        pixel_scale: int = 10,
        target_fps: int = 60,
        animations_module_name: str = "animations",
    ) -> None:
        self.grid_width: int = grid_width
        self.grid_height: int = grid_height
        self.pixel_scale: int = pixel_scale
        self.window_width_px: int = grid_width * pixel_scale
        self.window_height_px: int = grid_height * pixel_scale
        self.target_fps: int = target_fps

        self.animations_module_name: str = animations_module_name
        self.animations_module: Optional[ModuleType] = None
        self.animations: List[AnimationTuple] = []
        self.animations_path: Optional[str] = None
        self.animations_mtime: float = 0.0
        self.animations_dir: Optional[str] = None
        self.animations_tree_mtime: float = 0.0

        self.current_index: int = 0
        self.is_playing: bool = True
        self.show_grid: bool = True
        self.speed_multiplier: float = 1.0
        self.sim_time_seconds: float = 0.0
        self.frame_index: int = 0
        self.frame_buffer: np.ndarray = np.zeros(
            (self.grid_height, self.grid_width, 3), dtype=np.uint8
        )

        pygame.init()
        pygame.display.set_caption(f"{self.grid_width}x{self.grid_height} LED Animator")
        self.screen = pygame.display.set_mode(
            (self.window_width_px, self.window_height_px)
        )
        self.clock = pygame.time.Clock()
        try:
            self.font = pygame.font.SysFont("monospace", 14)
        except Exception:
            self.font = None

        self._load_animations(first_load=True)

    # ----------------------------- Animation Management ----------------------------- #
    def _load_animations(self, first_load: bool = False) -> None:
        """Import or reload the animations module and extract animations.

        Expects the module to define ANIMATIONS: List[Tuple[str, Callable[[int, float], np.ndarray]]].
        """
        try:
            if self.animations_module is None:
                # Initial import
                self.animations_module = importlib.import_module(
                    self.animations_module_name
                )
            else:
                # Reload existing module
                self.animations_module = importlib.reload(self.animations_module)
        except Exception:
            traceback.print_exc()
            if first_load:
                raise SystemExit("Failed to import animations module.")
            return

        # Resolve file path and mtime for hot-reload checks
        try:
            module_file = self.animations_module.__file__ or ""
            self.animations_path = os.path.abspath(module_file)
            self.animations_mtime = os.path.getmtime(self.animations_path)
        except Exception:
            self.animations_path = None
            self.animations_mtime = 0.0

        # If animations is a package, record its directory and tree mtime for hot-reload
        try:
            if (
                hasattr(self.animations_module, "__path__")
                and self.animations_module.__file__
            ):
                module_dir = os.path.dirname(self.animations_module.__file__)
                self.animations_dir = module_dir
                self.animations_tree_mtime = self._compute_tree_mtime(module_dir)
            else:
                self.animations_dir = None
                self.animations_tree_mtime = 0.0
        except Exception:
            self.animations_dir = None
            self.animations_tree_mtime = 0.0

        # Validate and load animations list
        loaded: List[AnimationTuple] = []
        try:
            exported = getattr(self.animations_module, "ANIMATIONS")
            if not isinstance(exported, list):
                raise TypeError("ANIMATIONS must be a list of (name, func) tuples")
            for item in exported:
                if (
                    isinstance(item, tuple)
                    and len(item) == 2
                    and isinstance(item[0], str)
                    and callable(item[1])
                ):
                    loaded.append((item[0], item[1]))
        except Exception:
            traceback.print_exc()
            if first_load:
                raise SystemExit("animations.ANIMATIONS is missing or invalid")
            return

        if not loaded:
            if first_load:
                raise SystemExit("No animations found in animations.ANIMATIONS")
            return

        previous_name = (
            self.animations[self.current_index][0] if self.animations else None
        )
        self.animations = loaded

        # Try to keep the same animation selected after reload
        if previous_name is not None:
            for idx, (name, _) in enumerate(self.animations):
                if name == previous_name:
                    self.current_index = idx
                    break
            else:
                self.current_index = 0

        # Reset time on load to avoid surprises
        if first_load:
            self.sim_time_seconds = 0.0
            self.frame_index = 0

    def _check_for_module_change(self) -> None:
        # Prefer directory-wide checks for packages to catch changes in any submodule
        if self.animations_dir:
            try:
                current_tree = self._compute_tree_mtime(self.animations_dir)
            except Exception:
                current_tree = 0.0
            if current_tree > self.animations_tree_mtime:
                self.animations_tree_mtime = current_tree
                self._load_animations(first_load=False)
                return

        if not self.animations_path:
            return
        try:
            current_mtime = os.path.getmtime(self.animations_path)
        except Exception:
            return
        if current_mtime > self.animations_mtime:
            self.animations_mtime = current_mtime
            self._load_animations(first_load=False)

    def _compute_tree_mtime(self, root_dir: str) -> float:
        latest = 0.0
        for dirpath, _, filenames in os.walk(root_dir):
            for fname in filenames:
                if not fname.endswith(".py"):
                    continue
                path = os.path.join(dirpath, fname)
                try:
                    m = os.path.getmtime(path)
                except Exception:
                    m = 0.0
                if m > latest:
                    latest = m
        return latest

    # ----------------------------------- Rendering ---------------------------------- #
    def _call_animation(
        self, func: GridFrameFunc, frame_index: int, t_seconds: float
    ) -> np.ndarray:
        try:
            func(frame_index, t_seconds, self.frame_buffer)
        except Exception:
            traceback.print_exc()
            return self._error_frame()

        # Validate buffer integrity
        fb = self.frame_buffer
        if (
            not isinstance(fb, np.ndarray)
            or fb.ndim != 3
            or fb.shape[:2] != (self.grid_height, self.grid_width)
            or fb.shape[2] != 3
        ):
            return self._error_frame()
        if fb.dtype != np.uint8:
            np.clip(fb, 0, 255, out=fb)
            self.frame_buffer = fb.astype(np.uint8, copy=False)
        return self.frame_buffer

    def _error_frame(self) -> np.ndarray:
        self.frame_buffer.fill(0)
        self.frame_buffer[:, :, 0] = 64
        return self.frame_buffer

    def _draw_grid(self) -> None:
        if not self.show_grid:
            return
        color = (48, 48, 48)
        step = self.pixel_scale
        width = max(2, self.pixel_scale // 8)
        for i in range(1, self.grid_width):
            x = i * step
            pygame.draw.line(
                self.screen, color, (x, 0), (x, self.window_height_px), width
            )
        for i in range(1, self.grid_height):
            y = i * step
            pygame.draw.line(
                self.screen, color, (0, y), (self.window_width_px, y), width
            )

    def _draw_overlay_text(self) -> None:
        if not self.font:
            return
        name = self.animations[self.current_index][0] if self.animations else "(none)"
        play_state = "Play" if self.is_playing else "Pause"
        text = f"{name} | {play_state} | Speed {self.speed_multiplier:.2f}x"
        try:
            surf = self.font.render(text, True, (255, 255, 255))
            self.screen.blit(surf, (8, 6))
        except Exception:
            pass

    def _render_frame(self, frame_array: np.ndarray) -> None:
        # surfarray expects (width, height, 3), our frame is (rows, cols, 3)
        arr = np.transpose(frame_array, (1, 0, 2))
        surf = pygame.surfarray.make_surface(arr)
        if self.pixel_scale != 1:
            surf = pygame.transform.scale(
                surf, (self.window_width_px, self.window_height_px)
            )
        self.screen.blit(surf, (0, 0))
        self._draw_grid()
        self._draw_overlay_text()
        pygame.display.flip()

    # ------------------------------------ Input ------------------------------------- #
    def _next_animation(self) -> None:
        if not self.animations:
            return
        self.current_index = (self.current_index + 1) % len(self.animations)
        self.sim_time_seconds = 0.0
        self.frame_index = 0

    def _prev_animation(self) -> None:
        if not self.animations:
            return
        self.current_index = (self.current_index - 1) % len(self.animations)
        self.sim_time_seconds = 0.0
        self.frame_index = 0

    def _handle_keydown(self, key: int) -> None:
        if key in (pygame.K_ESCAPE, pygame.K_q):
            pygame.quit()
            raise SystemExit(0)
        if key == pygame.K_SPACE:
            self.is_playing = not self.is_playing
            return
        if key == pygame.K_RIGHT:
            self._next_animation()
            return
        if key == pygame.K_LEFT:
            self._prev_animation()
            return
        if key == pygame.K_UP:
            self.speed_multiplier = min(64.0, self.speed_multiplier * 1.25)
            return
        if key == pygame.K_DOWN:
            self.speed_multiplier = max(0.05, self.speed_multiplier / 1.25)
            return
        if key == pygame.K_g:
            self.show_grid = not self.show_grid
            return
        if key == pygame.K_r:
            self._load_animations(first_load=False)
            return

    # ------------------------------------- Main ------------------------------------- #
    def run(self) -> None:
        while True:
            self._check_for_module_change()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit(0)
                if event.type == pygame.KEYDOWN:
                    self._handle_keydown(event.key)

            dt_ms = self.clock.tick(self.target_fps)
            dt = dt_ms / 1000.0
            if self.is_playing:
                self.sim_time_seconds += dt * self.speed_multiplier
                self.frame_index += 1

            if not self.animations:
                pygame.display.set_caption("No animations loaded")
                self.screen.fill((16, 16, 16))
                pygame.display.flip()
                continue

            name, func = self.animations[self.current_index]
            pygame.display.set_caption(
                f"{self.grid_width}x{self.grid_height} LED Animator - {name}"
            )
            frame = self._call_animation(func, self.frame_index, self.sim_time_seconds)
            self._render_frame(frame)


def main() -> None:
    # Allow optional CLI overrides
    # Backwards compatibility: LED_GRID_SIZE sets both width and height if provided
    legacy_size = os.environ.get("LED_GRID_SIZE")
    default_width = 64
    default_height = 128
    grid_width = int(
        os.environ.get("LED_GRID_WIDTH", legacy_size or str(default_width))
    )
    grid_height = int(
        os.environ.get("LED_GRID_HEIGHT", legacy_size or str(default_height))
    )
    pixel_scale = int(os.environ.get("LED_PIXEL_SCALE", "10"))
    target_fps = int(os.environ.get("LED_TARGET_FPS", "60"))
    app = AnimatorApp(
        grid_width=grid_width,
        grid_height=grid_height,
        pixel_scale=pixel_scale,
        target_fps=target_fps,
    )
    app.run()


if __name__ == "__main__":
    main()
