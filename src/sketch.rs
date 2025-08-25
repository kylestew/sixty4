use crate::frame::Frame;

pub trait Sketch {
    /// Render the current frame for time `t` (seconds).
    fn render(&mut self, t: f32, frame: &mut Frame);
}
