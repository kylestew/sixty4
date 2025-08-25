use crate::sketch::Sketch;

pub struct Simple;
impl Sketch for Simple {
    fn render(&mut self, t: f32, frame: &mut crate::frame::Frame) {
        for y in 0..frame.h {
            for x in 0..frame.w {
                let nx = x as f32 / (frame.w as f32 - 1.0);
                let ny = y as f32 / (frame.h as f32 - 1.0);

                // moving band
                let v = ((nx + t * 0.25).fract() - ny).abs();
                let hue = (nx + t * 0.10).fract();

                let (r, g, b) = hsv_to_rgb(hue, 1.0, (1.0 - v * 2.0).clamp(0.0, 1.0));
                frame.put_rgb(
                    x,
                    y,
                    (r * 255.0) as u8,
                    (g * 255.0) as u8,
                    (b * 255.0) as u8,
                );
            }
        }
    }
}

// tiny HSV->RGB helper
fn hsv_to_rgb(h: f32, s: f32, v: f32) -> (f32, f32, f32) {
    let i = (h * 6.0).floor();
    let f = h * 6.0 - i;
    let p = v * (1.0 - s);
    let q = v * (1.0 - f * s);
    let t = v * (1.0 - (1.0 - f) * s);
    match (i as i32) % 6 {
        0 => (v, t, p),
        1 => (q, v, p),
        2 => (p, v, t),
        3 => (p, q, v),
        4 => (t, p, v),
        _ => (v, p, q),
    }
}
