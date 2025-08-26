use crate::color::hsv_to_rgb;
use crate::sketch::Sketch;

pub struct Plasma;
impl Sketch for Plasma {
    fn render(&mut self, t: f32, frame: &mut crate::frame::Frame) {
        for (x, y, u, v) in frame.iter() {
            // horizontal + vertical
            let w1 = (8.0 * u + t * 0.8).sin();
            let w2 = (8.0 * v + t * 0.9).sin();

            // radial
            let dx = u - 0.5;
            let dy = v - 0.5;
            let r = (dx * dx + dy * dy).sqrt();
            let w3 = (10.0 * r - t * 0.7).sin();

            // combine + normalize
            let c = (w1 + w2 + w3) / 3.0;
            let hue = 0.5 + 0.5 * c; // map to [0,1]

            let (r, g, b) = hsv_to_rgb(hue.fract(), 1.0, 1.0);

            frame.put_rgb_f32(x, y, r, g, b);
        }
    }
}
