pub struct Frame {
    pub w: u32,
    pub h: u32,
    pub data: Vec<u8>, // RGBA8
}

impl Frame {
    pub fn new(w: u32, h: u32) -> Self {
        Self {
            w,
            h,
            data: vec![0; (w * h * 4) as usize],
        }
    }
    #[inline]
    pub fn put_rgb(&mut self, x: u32, y: u32, r: u8, g: u8, b: u8) {
        if x >= self.w || y >= self.h {
            return;
        }
        let idx = ((y * self.w + x) * 4) as usize;
        self.data[idx] = r;
        self.data[idx + 1] = g;
        self.data[idx + 2] = b;
        self.data[idx + 3] = 255; // opaque alpha
    }
}
