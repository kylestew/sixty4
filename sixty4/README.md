# sixty4

Minimal graphics sandbox. Ships as a library by default. A desktop viewer binary is available behind an opt-in feature.

## Requirements
- Rust (stable)

## Build (library only)
No GUI dependencies are pulled unless you enable the feature.

```bash
cargo build
```

## Run the desktop viewer
The desktop binary is gated behind the `desktop` feature.

```bash
# dev run
cargo run --features desktop

# or explicitly
cargo run --bin desktop --features desktop

# release build
cargo build --release --features desktop
```

## Use as a dependency
By default you get the pure library (no desktop deps).

```toml
[dependencies]
sixty4 = "0.1.0"
```

If you want to depend on the crate and build the desktop binary in your workspace, enable the feature when invoking binaries:

```bash
cargo run -p sixty4 --bin desktop --features desktop
```

## Notes
- The `desktop` feature enables optional dependencies: `anyhow`, `winit`, and `pixels`.
- The default run target is `desktop`, so running without the feature will instruct you to enable it.
