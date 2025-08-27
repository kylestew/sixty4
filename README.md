## sixty4

Tiny 64×64 rendering playground for generative sketches and embedded displays. Workspace layout: `core` (library + examples) and `firmware` (embedded). The `core` crate provides a small `Frame` buffer and a `Sketch` trait. The desktop runner lives under `core/examples/` using `winit` + `pixels` to visualize frames at pixel-perfect scale.

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
cd sixty4
cargo run --example desktop
```

Run with optimizations:
```bash
cargo run --example desktop --release
```

### Switching sketches in the desktop example
Open `core/examples/desktop.rs` and change the alias used for `MySketch`.

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
core/
  src/
    color.rs        # tiny HSV -> RGB helper
    frame.rs        # Frame buffer + iterator
    sketch.rs       # Sketch trait
    sketches/       # built-in sketches
      plasma.rs
      simple.rs
    lib.rs          # library entry
  examples/
    desktop.rs      # desktop runner (winit + pixels)
firmware/
  src/
    main.rs         # embedded-oriented stub main
```

### Embedded use
- `firmware/src/main.rs` is intentionally minimal so the embedded crate can be integrated into targets without pulling desktop windowing dependencies.
- Use the `Frame` type and your `Sketch` to drive your display (e.g., an LED matrix). The `core` crate uses `std` (e.g., `Vec<u8>`); ensure your target provides an allocator if you integrate `core` into no_std firmware.


