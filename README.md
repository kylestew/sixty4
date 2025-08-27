## sixty4

Tiny 64×64 rendering playground for generative sketches and embedded displays. Workspace layout: `sixty4` (library + desktop runner) and `firmware` (embedded). The `sixty4` crate provides a small `Frame` buffer and a `Sketch` trait. The desktop runner lives under `sixty4/src/bin/` using `winit` + `pixels` to visualize frames at pixel-perfect scale.

### Features
- **Minimal API**: `Frame` (RGBA8 buffer), `Sketch` trait with `render(t, frame)`.
- **Examples included**: `plasma` and `simple` sketches.
- **Embedded-friendly**: the `firmware` crate contains an embedded-oriented stub; desktop rendering stays in `core/examples` and is not a dependency of firmware.

### Requirements
- Rust toolchain (stable is fine).
- Desktop example requires a platform windowing stack (macOS, Linux, Windows).

### Quickstart
```bash
git clone https://github.com/your-org/sixty4
cd sixty4/sixty4
cargo run --features desktop
```

Run with optimizations:
```bash
cargo run --features desktop --release
```

### Switching sketches in the desktop binary
Open `sixty4/src/bin/desktop.rs` and change the alias used for `MySketch`.

Current:
```rust
use sixty4::sketches::plasma::Plasma as MySketch;
```

Switch to the simple sketch:
```rust
use sixty4::sketches::simple::Simple as MySketch;
```

### Write your own sketch
Implement the `Sketch` trait and use `Frame` helpers to write pixels.

```rust
use sixty4::frame::Frame;
use sixty4::sketch::Sketch;

pub struct MySketch;

impl Sketch for MySketch {
    fn render(&mut self, t: f32, frame: &mut Frame) {
        for (x, y, u, v) in frame.iter() {
            let r = (u + t.sin() * 0.5 + 0.5).fract();
            let g = (v + t.cos() * 0.5 + 0.5).fract();
            let b = 0.2;
            frame.put_rgb_f32(x, y, r, g, b);
        }
    }
}
```

Then point the desktop example at it:
```rust
use your_module::MySketch as MySketch;
```

### Project layout
```
sixty4/
  src/
    color.rs        # tiny HSV -> RGB helper
    frame.rs        # Frame buffer + iterator
    sketch.rs       # Sketch trait
    sketches/       # built-in sketches
      plasma.rs
      simple.rs
    lib.rs          # library entry
    bin/
      desktop.rs    # desktop runner (winit + pixels)
firmware/
  src/
    main.rs         # embedded-oriented stub main
```

### Embedded use
- `firmware/src/main.rs` is intentionally minimal so the embedded crate can be integrated into targets without pulling desktop windowing dependencies.
- Use the `Frame` type and your `Sketch` to drive your display (e.g., an LED matrix). The `sixty4` crate currently uses `std` (e.g., `Vec<u8>`); if you reference it from `firmware`, ensure your target provides an allocator or refactor to a caller-provided buffer. The firmware now references `sixty4` via a path dependency.


