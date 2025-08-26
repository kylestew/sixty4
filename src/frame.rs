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
    #[inline]
    pub fn put_rgb_f32(&mut self, x: u32, y: u32, r: f32, g: f32, b: f32) {
        if x >= self.w || y >= self.h {
            return;
        }

        #[inline]
        fn to_u8(v: f32) -> u8 {
            let v = v.max(0.0).min(1.0);
            (v * 255.0 + 0.5) as u8
        }

        let idx = ((y * self.w + x) as usize) * 4;
        self.data[idx] = to_u8(r);
        self.data[idx + 1] = to_u8(g);
        self.data[idx + 2] = to_u8(b);
        self.data[idx + 3] = 255;
    }

    pub fn iter(&self) -> FrameIter {
        FrameIter {
            w: self.w,
            h: self.h,
            i: 0,
        }
    }
}

pub struct FrameIter {
    w: u32,
    h: u32,
    i: u32,
}

impl Iterator for FrameIter {
    type Item = (u32, u32, f32, f32); // (x, y, u, v)

    fn next(&mut self) -> Option<Self::Item> {
        let y = self.i / self.w;
        let x = self.i - y * self.w; // cheaper than i % w sometimes

        if y >= self.h {
            return None;
        }

        // normalized coords in [0, 1]
        let u = x as f32 / (self.w.saturating_sub(1).max(1)) as f32;
        let v = y as f32 / (self.h.saturating_sub(1).max(1)) as f32;

        // increment
        self.i += 1;

        Some((x, y, u, v))
    }
}
