#![no_std]
#![no_main]

use panic_probe as _;
use rp235x_hal::entry;

#[entry]
fn main() -> ! {
    loop {}
}
