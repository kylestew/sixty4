use anyhow;
use pixels::{Pixels, SurfaceTexture};
use std::sync::Arc;
use std::time::Instant;
use winit::{
    dpi::LogicalSize,
    event::{Event, WindowEvent},
    event_loop::EventLoop,
    window::{Window, WindowBuilder},
};

mod frame;
mod sketch;
mod sketches;

use frame::Frame;
use sketch::Sketch;
use sketches::simple::Simple;

const W: u32 = 64;
const H: u32 = 64;
const SCALE: f64 = 12.0; // upscale factor

fn run(event_loop: EventLoop<()>, window: Window) {
    let window = Arc::new(window); // why arc? who else needs this?
    let mut pixels = {
        let size = window.inner_size();
        let surface = SurfaceTexture::new(size.width, size.height, &*window);
        Pixels::new(W, H, surface).unwrap()
    };

    // why need a clone?
    let redraw_window = window.clone();

    // --- animation state ---
    let mut frame = Frame::new(W, H);
    let mut sketch: Box<dyn Sketch> = Box::new(Simple);
    let start = Instant::now();

    event_loop
        .run(move |event, target| match event {
            Event::WindowEvent { event, .. } => match event {
                WindowEvent::CloseRequested => target.exit(),
                WindowEvent::Resized(new_size) => {
                    let _ = pixels.resize_surface(new_size.width, new_size.height);
                }
                WindowEvent::RedrawRequested => {
                    // time in seconds
                    let t = (Instant::now() - start).as_secs_f32();

                    // render into our 64x64 RGBA buffer
                    sketch.render(t, &mut frame);

                    // blit to pixels and present
                    let fb = pixels.frame_mut();
                    fb.copy_from_slice(&frame.data);

                    if let Err(e) = pixels.render() {
                        eprintln!("pixels error: {e}");
                        target.exit();
                    }
                }
                _ => {}
            },
            // drive the redraws (vsync will pace to ~60fps)
            Event::AboutToWait => {
                redraw_window.request_redraw();
            }
            _ => {}
        })
        .unwrap();
}

fn main() -> anyhow::Result<()> {
    let event_loop = EventLoop::new()?;
    let size = LogicalSize::new((W as f64) * SCALE, (H as f64) * SCALE);
    let window = WindowBuilder::new()
        .with_title("sixty4")
        .with_inner_size(size)
        .with_min_inner_size(LogicalSize::new(128.0, 128.0))
        .build(&event_loop)?;
    run(event_loop, window);
    Ok(()) // unreachable
}
