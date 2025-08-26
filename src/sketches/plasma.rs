use crate::sketch::Sketch;

pub struct Plasma;
impl Sketch for Plasma {
    fn render(&mut self, _t: f32, frame: &mut crate::frame::Frame) {
        for (x, y, u, v) in frame.iter() {
            frame.put_rgb(x, y, (u * 255.0) as u8, (v * 255.0) as u8, 0);
        }
    }
}
