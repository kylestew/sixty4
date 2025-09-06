//! Controls an SK6812 RGB LED on GPIO18
//!
//! This will cycle through red, green, and blue colors every second.
#![no_std]
#![no_main]

use defmt::*;
use defmt_rtt as _;
use panic_probe as _;
use rp235x_hal::clocks::init_clocks_and_plls;
use rp235x_hal::pio::{PIOExt, Running, SM0, StateMachine, Tx, UninitStateMachine};
use rp235x_hal::{self as hal, entry};
use rp235x_hal::{Clock, pac};

use smart_leds::RGB8;

// Provide an alias for our BSP so we can switch targets quickly.
// Uncomment the BSP you included in Cargo.toml, the rest of the code does not need to change.
// use some_bsp;

/// Tell the Boot ROM about our application
#[unsafe(link_section = ".start_block")]
#[used]
pub static IMAGE_DEF: hal::block::ImageDef = hal::block::ImageDef::secure_exe();

/// SK6812 LED driver using PIO
struct Sk6812 {
    tx: Tx<(pac::PIO0, SM0)>,
    _sm: StateMachine<(pac::PIO0, SM0), Running>,
}

impl Sk6812 {
    fn new(
        pio: &mut hal::pio::PIO<pac::PIO0>,
        sm: UninitStateMachine<(pac::PIO0, SM0)>,
        pin: hal::gpio::Pin<hal::gpio::bank0::Gpio18, hal::gpio::FunctionPio0, hal::gpio::PullNone>,
        clock_freq: hal::fugit::HertzU32,
    ) -> Self {
        // SK6812 timing: 1.25us per bit, ~800kHz
        // 0 = 0.3us high, 0.9us low
        // 1 = 0.9us high, 0.3us low
        let div = (clock_freq.to_Hz() as f32 / 800_000.0 / 3.0) as u16;

        // PIO program for SK6812
        // This is a simple bit-banging program
        let program = pio_proc::pio_asm!(
            ".side_set 1",
            ".wrap_target",
            "bitloop:",
            "   out x, 1       side 0 [2]",  // Get next bit, drive low
            "   jmp !x, do_zero side 1 [1]", // Drive high, branch on bit value
            "do_one:",
            "   jmp bitloop    side 1 [1]", // Drive high for 1
            "do_zero:",
            "   nop            side 0 [1]", // Drive low for 0
            ".wrap",
        );

        let installed = pio.install(&program.program).unwrap();
        let (mut sm, _, tx) = hal::pio::PIOBuilder::from_installed_program(installed)
            .out_pins(pin.id().num, 1)
            .side_set_pin_base(pin.id().num)
            .clock_divisor_fixed_point(div, 0)
            .out_shift_direction(hal::pio::ShiftDirection::Left)
            .autopull(true)
            .pull_threshold(24)
            .build(sm);

        sm.set_pindirs([(pin.id().num, hal::pio::PinDir::Output)]);
        let sm = sm.start();

        Self { tx, _sm: sm }
    }

    fn write(&mut self, color: RGB8) {
        // SK6812 expects GRB order
        let data = ((color.g as u32) << 16) | ((color.r as u32) << 8) | (color.b as u32);

        // Write to the PIO FIFO
        // The write method is available directly on tx
        while !self.tx.write(data) {}
    }
}

#[entry]
fn main() -> ! {
    info!("Program start");
    let mut pac = pac::Peripherals::take().unwrap();
    let core = cortex_m::Peripherals::take().unwrap();
    let mut watchdog = hal::Watchdog::new(pac.WATCHDOG);
    let sio = hal::Sio::new(pac.SIO);

    // External high-speed crystal on the pico board is 12Mhz
    let external_xtal_freq_hz = 12_000_000u32;
    let clocks = init_clocks_and_plls(
        external_xtal_freq_hz,
        pac.XOSC,
        pac.CLOCKS,
        pac.PLL_SYS,
        pac.PLL_USB,
        &mut pac.RESETS,
        &mut watchdog,
    )
    .ok()
    .unwrap();

    let mut delay = cortex_m::delay::Delay::new(core.SYST, clocks.system_clock.freq().to_Hz());

    let pins = hal::gpio::Pins::new(
        pac.IO_BANK0,
        pac.PADS_BANK0,
        sio.gpio_bank0,
        &mut pac.RESETS,
    );

    // Configure GPIO18 for PIO
    let led_pin = pins
        .gpio18
        .into_function::<hal::gpio::FunctionPio0>()
        .into_pull_type();

    // Initialize PIO for the SK6812 LED
    let (mut pio, sm0, _, _, _) = pac.PIO0.split(&mut pac.RESETS);
    let mut sk6812 = Sk6812::new(&mut pio, sm0, led_pin, clocks.system_clock.freq());

    // Define the colors to cycle through
    let colors = [
        RGB8::new(255, 0, 0), // Red
        RGB8::new(0, 255, 0), // Green
        RGB8::new(0, 0, 255), // Blue
    ];

    let mut color_index = 0;

    loop {
        // Get the current color
        let color = colors[color_index];

        // Display the color on the LED
        info!("Setting color: R={}, G={}, B={}", color.r, color.g, color.b);
        sk6812.write(color);

        // Wait for transmission to complete (reset time)
        delay.delay_us(80);

        // Wait for 1 second
        delay.delay_ms(1000);

        // Move to the next color
        color_index = (color_index + 1) % colors.len();
    }
}

/// Program metadata for `picotool info`
#[unsafe(link_section = ".bi_entries")]
#[used]
pub static PICOTOOL_ENTRIES: [rp235x_hal::binary_info::EntryAddr; 5] = [
    rp235x_hal::binary_info::rp_cargo_bin_name!(),
    rp235x_hal::binary_info::rp_cargo_version!(),
    rp235x_hal::binary_info::rp_program_description!(c"SK6812 RGB LED Controller"),
    rp235x_hal::binary_info::rp_cargo_homepage_url!(),
    rp235x_hal::binary_info::rp_program_build_attribute!(),
];

// End of file
